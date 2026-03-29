from fastapi import APIRouter, Query
from fastapi import HTTPException
from pymongo import MongoClient
from bson import ObjectId
from config import MONGO_URI

router = APIRouter()
db = MongoClient(MONGO_URI)["patchpilot"]

@router.get("/jobs")
def list_jobs(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=200)):
    cursor = db["contributions"].find({}, {"logs": 0}).sort("created_at", -1).skip(skip).limit(limit)
    jobs = list(cursor)
    for j in jobs:
        j["_id"] = str(j["_id"])
    total = db["contributions"].count_documents({})
    return {"total": total, "items": jobs, "skip": skip, "limit": limit}

@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = db["contributions"].find_one({"_id": ObjectId(job_id)})
    job["_id"] = str(job["_id"])
    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    result = db["contributions"].delete_one({"_id": ObjectId(job_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"deleted": True, "job_id": job_id}
