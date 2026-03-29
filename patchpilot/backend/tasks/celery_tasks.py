from celery_app import celery
from pymongo import MongoClient
from services.repo_scanner import build_snapshot
from services.ai_service import analyze_repo
from services.github_service import run_contribution
from config import MONGO_URI
from datetime import datetime
from bson import ObjectId

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
