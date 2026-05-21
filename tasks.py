import os
import json
from celery import Celery
from main import run_pipeline

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

JOBS_DIR = "jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

def update_job_status(job_id: str, status: str, progress: int, message: str = ""):
    job_file = os.path.join(JOBS_DIR, f"{job_id}.json")
    if os.path.exists(job_file):
        with open(job_file, "r", encoding="utf-8") as f:
            job_data = json.load(f)
    else:
        job_data = {"job_id": job_id}
        
    job_data.update({
        "status": status,
        "progress": progress,
        "message": message
    })
    
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)

@celery_app.task(bind=True)
def process_podcast_task(self, job_id: str, url: str):
    update_job_status(job_id, "RUNNING", 5, "Starting processing pipeline...")
    try:
        # Pass job_id so run_pipeline can update its own steps if needed, 
        # but for now run_pipeline runs synchronously within this worker.
        run_pipeline(url, resume=False, full=True, job_id=job_id)
        update_job_status(job_id, "COMPLETED", 100, "Podcast processed successfully.")
    except Exception as e:
        update_job_status(job_id, "FAILED", 0, f"Error: {str(e)}")
        raise e
