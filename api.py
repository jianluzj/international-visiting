from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os
import uuid
import time
from config import settings
from tasks import process_podcast_task

app = FastAPI(title="International Visiting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    url: str

JOBS_DIR = "jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

def get_processed_podcasts():
    db_path = os.path.join(settings.processed_dir, "processed_episodes.json")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.post("/api/jobs")
async def create_job(req: JobRequest):
    if not req.url or "apple.com" not in req.url:
        raise HTTPException(status_code=400, detail="Invalid Apple Podcasts URL")
    
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "url": req.url,
        "status": "PENDING",
        "progress": 0,
        "message": "Task queued.",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(os.path.join(JOBS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)
    
    # Send task to Celery
    process_podcast_task.delay(job_id, req.url)
    
    return {"job_id": job_id, "message": "Job created successfully."}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    job_file = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(job_file):
        raise HTTPException(status_code=404, detail="Job not found")
    with open(job_file, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/podcasts")
async def list_podcasts():
    db = get_processed_podcasts()
    sorted_episodes = sorted(db.values(), key=lambda x: x.get('pub_date', ''), reverse=True)
    return sorted_episodes

@app.get("/")
async def root():
    return {"message": "Welcome to International Visiting API. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
