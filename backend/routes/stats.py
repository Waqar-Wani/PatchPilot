from fastapi import APIRouter
from pymongo import MongoClient
from config import MONGO_URI

router = APIRouter()
db = MongoClient(MONGO_URI)["patchpilot"]

@router.get("/stats")
def stats():
    docs = list(db["contributions"].find().sort("created_at", -1))
    summary = {
        "total": len(docs),
        "done": sum(1 for d in docs if d.get("status") == "Done"),
        "skipped": sum(1 for d in docs if d.get("status") == "Skipped"),
        "failed": sum(1 for d in docs if d.get("status") == "Failed"),
    }
    cost = sum((d.get("metrics", {}).get("cost_usd") or 0) for d in docs)
    summary["total_cost_usd"] = cost
    summary["avg_cost_per_fix"] = cost / summary["done"] if summary["done"] else None

    # project a lightweight list
    rows = []
    for d in docs:
        rows.append({
            "repo": d.get("repo_url"),
            "status": d.get("status"),
            "action": d.get("action"),
            "severity": d.get("metrics", {}).get("severity"),
            "files": d.get("metrics", {}).get("files"),
            "changes": d.get("metrics", {}).get("changes"),
            "pr_url": d.get("pr_url"),
            "branch": d.get("branch"),
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
            "tokens_used": d.get("metrics", {}).get("tokens_used"),
            "cost_usd": d.get("metrics", {}).get("cost_usd"),
        })

    return {"summary": summary, "runs": rows}
