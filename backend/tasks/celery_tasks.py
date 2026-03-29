from celery_app import celery
from pymongo import MongoClient
from services.repo_scanner import build_snapshot
from services.ai_service import analyze_repo
from services.github_service import run_contribution
from config import MONGO_URI
from datetime import datetime
from bson import ObjectId
import uuid

db = MongoClient(MONGO_URI)["patchpilot"]

@celery.task(bind=True)
def process_contribution(self, job_id: str, repo_url: str, mode: str, history: list):

    def log(msg: str):
        entry = {"time": datetime.utcnow().isoformat(), "msg": msg}
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

        log("Analyzing with Claude")
        result = analyze_repo(snapshot)

        # Fallback: if secrets are present but AI chose to skip or didn't plan removals, enforce security remediation.
        sensitive = snapshot.get("sensitive_files") or []
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

        if result["action"] == "SKIP":
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

        log("Claude approved — making contribution")
        pr_url = run_contribution(repo_url, result, log)

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
