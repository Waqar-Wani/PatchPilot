from fastapi import APIRouter
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from models.contribution import new_contribution
from tasks.celery_tasks import process_contribution
from config import MONGO_URI

router = APIRouter()
db = MongoClient(MONGO_URI)["patchpilot"]

class ContributeRequest(BaseModel):
    repo_url: str

@router.post("/contribute")
def contribute(req: ContributeRequest):
    history = db["contributions"].distinct("repo_url", {"status": "Done"})
    job     = new_contribution(req.repo_url, mode="manual")
    result  = db["contributions"].insert_one(job)
    job_id  = str(result.inserted_id)
    process_contribution.delay(job_id, req.repo_url, "manual", history)
    return {"job_id": job_id}
