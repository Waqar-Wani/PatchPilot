from fastapi import APIRouter
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from models.contribution import new_contribution
from tasks.celery_tasks import process_contribution
from config import MONGO_URI, GITHUB_TOKEN
from github import Github

router = APIRouter()
db = MongoClient(MONGO_URI)["patchpilot"]
g = Github(GITHUB_TOKEN)

class ContributeRequest(BaseModel):
    repo_url: str

@router.post("/contribute")
def contribute(req: ContributeRequest):
    # pick mode based on repo permissions: push allowed -> manual, else fork
    mode = "manual"
    try:
        name = req.repo_url.replace("https://github.com/", "").strip("/")
        repo = g.get_repo(name)
        if not getattr(repo.permissions, "push", False):
            mode = "fork_and_pr"
    except Exception:
        mode = "fork_and_pr"  # safe default

    history = db["contributions"].distinct("repo_url", {"status": "done"})
    job     = new_contribution(req.repo_url, mode=mode)
    result  = db["contributions"].insert_one(job)
    job_id  = str(result.inserted_id)
    process_contribution.delay(job_id, req.repo_url, mode, history)
    return {"job_id": job_id}
