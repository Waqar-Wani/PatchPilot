from celery_app import celery
from pymongo import MongoClient
from services.repo_scanner import build_snapshot
from services.ai_service import analyze_repo
from services.github_service import run_contribution
from config import MONGO_URI
from datetime import datetime
from bson import ObjectId
import uuid

SENSITIVE_HINTS = ("secret", "credential", "token", "key", ".env", ".pem", ".pfx", ".p12", ".keystore")

db = MongoClient(MONGO_URI)["patchpilot"]

@celery.task(bind=True)
def process_contribution(self, job_id: str, repo_url: str, mode: str, history: list):

    def log(msg: str):
        entry = {"time": datetime.utcnow().isoformat(), "msg": msg}
        # also emit to stdout for live visibility in worker terminal
        print(f"[job {job_id}] {msg}", flush=True)
        db["contributions"].update_one(
            {"_id": ObjectId(job_id)},
            {"$push": {"logs": entry}, "$set": {"updated_at": datetime.utcnow()}}
        )

    try:
        db["contributions"].update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "running"}}
        )

        log("Building repo snapshot")
        snapshot = build_snapshot(repo_url, history)

        log("Analyzing with AI")
        result = analyze_repo(snapshot)

        # Ensure git block exists with sane defaults
        result.setdefault("git", {})
        if not result["git"].get("branch_name"):
            result["git"]["branch_name"] = f"patchpilot/auto-{uuid.uuid4().hex[:6]}"
        result["git"].setdefault("commit_message", "PatchPilot automatic contribution")
        result["git"].setdefault("pr_title", "PatchPilot automatic contribution")
        result["git"].setdefault("pr_body", "This PR was created by PatchPilot.")
        result.setdefault("changes", [])
        result.setdefault("analysis", {})
        result["analysis"].setdefault("contribution_type", "general")
        result.setdefault("confidence", 0.5)
        result.setdefault("action", "SKIP")

        # Fallback: if secrets are present but AI chose to skip or didn't plan removals, enforce security remediation.
        sensitive = snapshot.get("sensitive_files") or []
        if not sensitive:
            # Fallback: detect by filename hints in file_tree
            for line in (snapshot.get("file_tree") or "").splitlines():
                low = line.lower()
                if any(h in low for h in ("secret", "credential", "token", "key", ".env", ".pem", ".pfx", ".p12", ".keystore")):
                    sensitive.append({"path": line.strip(), "content": ""})
        log(f"Sensitive files detected: {len(sensitive)}")

        if sensitive:
            if result.get("action") == "SKIP":
                result["action"] = "CONTRIBUTE"
                result["skip_reason"] = None
            result.setdefault("analysis", {}).setdefault("contribution_type", "security")
            result.setdefault("git", {})
            result["git"].setdefault("branch_name", f"patchpilot/remove-secrets-{uuid.uuid4().hex[:6]}")
            result["git"].setdefault("commit_message", "Remove committed secrets and add security findings")
            result["git"].setdefault("pr_title", "Remove committed secrets and add security findings")
            result["git"].setdefault("pr_body", "This PR removes committed secrets, adds `.gitignore` entry, and documents findings in SECURITY_FINDINGS.md.")
            result.setdefault("changes", [])

            # delete offending files
            for f in sensitive:
                result["changes"].append({
                    "change_type": "delete",
                    "file_path": f["path"],
                    "original_snippet": None,
                    "replacement_snippet": ""
                })

            # ensure .gitignore contains the paths
            gitignore_lines = "\n".join([p["path"] for p in sensitive]) + "\n"
            result["changes"].append({
                "change_type": "edit",
                "file_path": ".gitignore",
                "original_snippet": "",
                "replacement_snippet": gitignore_lines
            })

            # create/update security findings
            findings = "# Security Findings\n\n"
            for f in sensitive:
                findings += f"- Removed committed secret file `{f['path']}`.\n"
            findings += "\nRecommendation: rotate any exposed credentials and keep secrets out of the repo.\n"
            result["changes"].append({
                "change_type": "create",
                "file_path": "SECURITY_FINDINGS.md",
                "original_snippet": None,
                "replacement_snippet": findings
            })
            # allow deletion only for the sensitive files we detected
            result["allowed_deletes"] = [f["path"] for f in sensitive]
            log("Security remediation plan assembled")

        # Evidence gate: only proceed if we have a verified issue (sensitive files)
        evidence_present = bool(sensitive)
        if not evidence_present:
            log("No evidence found; skipping")
            db["contributions"].update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status":      "skipped",
                    "action":      "SKIP",
                    "skip_reason": "No actionable issue found",
                    "updated_at":  datetime.utcnow()
                }}
            )
            return

        # Validate changes for safety and completeness
        def abort_skip(reason: str):
            log(reason)
            db["contributions"].update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status":      "skipped",
                    "action":      "SKIP",
                    "skip_reason": reason,
                    "updated_at":  datetime.utcnow()
                }}
            )
            return "SKIPPED"

        if not result["changes"] or len(result["changes"]) == 0:
            if abort_skip("Empty patch") == "SKIPPED":
                return

        allowed_deletes = result.get("allowed_deletes", [])

        for change in result["changes"]:
            ctype = change.get("change_type")
            if ctype not in {"create", "edit", "delete"}:
                if abort_skip(f"Invalid change type: {ctype}") == "SKIPPED":
                    return
            else:
                log(f"Validating change: {ctype} {change.get('file_path')}")

            # Strict None/empty checks
            if ctype in {"create", "edit"}:
                content = change.get("replacement_snippet")
                if content is None or str(content).strip() == "":
                    if abort_skip(f"Empty content for {ctype} on {change.get('file_path')}") == "SKIPPED":
                        return
            if ctype == "edit":
                if change.get("original_snippet") is None:
                    if abort_skip(f"Missing original_snippet for edit on {change.get('file_path')}") == "SKIPPED":
                        return
            if ctype == "delete":
                if change.get("file_path") not in allowed_deletes:
                    if abort_skip(f"Unsafe operation: deletion not allowed for {change.get('file_path')}") == "SKIPPED":
                        return
        log("All changes validated; proceeding to run contribution")

        if result["action"] == "SKIP":
            log(f"AI returned SKIP: {result.get('skip_reason')}")
            db["contributions"].update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status":      "skipped",
                    "action":      "SKIP",
                    "skip_reason": result.get("skip_reason"),
                    "updated_at":  datetime.utcnow()
                }}
            )
            return

        log("AI approved — making contribution")
        pr_url = run_contribution(repo_url, result, log, mode)

        db["contributions"].update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {
                "status":            "done",
                "action":            "CONTRIBUTE",
                "pr_url":            pr_url,
                "pr_title":          result["git"]["pr_title"],
                "branch":            result["git"]["branch_name"],
                "contribution_type": result["analysis"]["contribution_type"],
                "confidence":        result["confidence"],
                "updated_at":        datetime.utcnow()
            }}
        )

    except Exception as e:
        log(f"Error: {str(e)}")
        db["contributions"].update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
        )
