"""FastAPI app: matchup API and pipeline trigger."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import MatchupRequest, PipelineJob, PipelineStatus
from app.pipeline import goat_matchup_pipeline, get_job_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if needed


app = FastAPI(
    title="GOAT Matchup Video Generator",
    description="Automated pipeline: matchup → script → clips → voice → assembly → thumbnail → YouTube",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/matchup/run", response_model=dict)
def run_matchup(request: MatchupRequest, background_tasks: BackgroundTasks):
    """Start the full pipeline in the background. Returns job_id for polling."""
    from prefect.deployments import run_deployment
    # Run the Prefect flow synchronously in-process for simplicity (blocking).
    # For production, use Prefect worker + run_deployment to run in background.
    try:
        result = goat_matchup_pipeline(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/matchup/run-async", response_model=dict)
def run_matchup_async(request: MatchupRequest, background_tasks: BackgroundTasks):
    """Start the pipeline in background; returns job_id immediately. Poll /api/jobs/{job_id}."""
    import threading
    import uuid as u
    job_id = str(u.uuid4())[:8]
    store = get_job_store()
    store[job_id] = {
        "job_id": job_id,
        "request": request.model_dump(),
        "status": PipelineStatus.PENDING.value,
        "script": None,
        "video_path": None,
        "thumbnail_path": None,
        "youtube_url": None,
        "error": None,
    }

    def run():
        try:
            goat_matchup_pipeline(request, job_id=job_id)
        except Exception as e:
            store[job_id]["status"] = PipelineStatus.FAILED.value
            store[job_id]["error"] = str(e)

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    return {"job_id": job_id, "message": "Pipeline started. Poll GET /api/jobs/" + job_id + " for status."}


@app.get("/api/jobs/{job_id}", response_model=dict)
def get_job(job_id: str):
    """Get pipeline job status and result."""
    store = get_job_store()
    if job_id not in store:
        raise HTTPException(status_code=404, detail="Job not found")
    return store[job_id]


@app.get("/api/jobs")
def list_jobs():
    """List all pipeline jobs."""
    return list(get_job_store().values())
