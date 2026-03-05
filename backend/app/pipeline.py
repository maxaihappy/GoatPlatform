"""Prefect flow: full GOAT matchup pipeline from request to YouTube."""
import uuid
from pathlib import Path
from typing import Optional, List

from prefect import flow, task

from app.config import get_settings
from app.models import MatchupRequest, MatchupScript, PipelineStatus
from app.services.script_generator import ScriptGenerator
from app.services.video_generator import VideoGenerator
from app.services.voice_generator import VoiceGenerator
from app.services.video_assembly import VideoAssembly
from app.services.thumbnail_generator import ThumbnailGenerator
from app.services.youtube_upload import YouTubeUploader


# In-memory job store for demo; replace with DB/Redis in production
_job_store: dict[str, dict] = {}


def get_job_store():
    return _job_store


@task
def generate_script(request: MatchupRequest) -> MatchupScript:
    gen = ScriptGenerator()
    return gen.generate(request)


@task
def generate_clips(script: MatchupScript) -> List[str]:
    gen = VideoGenerator()
    return gen.generate_clips(script)


@task
def generate_voice(script: MatchupScript, job_id: str) -> str:
    gen = VoiceGenerator()
    path = Path(get_settings().storage_path) / "audio" / f"{job_id}_commentary.mp3"
    return gen.generate(script, output_path=str(path))


@task
def assemble_video(
    clip_paths: List[str],
    commentary_path: str,
    script: MatchupScript,
    job_id: str,
) -> str:
    asm = VideoAssembly()
    return asm.assemble(
        clip_paths=clip_paths,
        commentary_audio_path=commentary_path,
        script=script,
        output_filename=f"{job_id}_goat_matchup.mp4",
    )


@task
def generate_thumbnail(request: MatchupRequest, script: MatchupScript, job_id: str) -> str:
    gen = ThumbnailGenerator()
    return gen.generate(
        request=request,
        script=script,
        output_filename=f"{job_id}_thumbnail.png",
    )


@task
def upload_to_youtube(
    video_path: str,
    thumbnail_path: str,
    script: MatchupScript,
) -> str:
    uploader = YouTubeUploader()
    return uploader.upload(
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        script=script,
    )


@flow(name="goat-matchup-pipeline", log_prints=True)
def goat_matchup_pipeline(request: MatchupRequest, job_id: Optional[str] = None) -> dict:
    """Run the full pipeline: script → clips → voice → assembly → thumbnail → (optional) YouTube."""
    job_id = job_id or str(uuid.uuid4())[:8]
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

    try:
        store[job_id]["status"] = PipelineStatus.SCRIPT.value
        script = generate_script(request)
        store[job_id]["script"] = script.model_dump()

        store[job_id]["status"] = PipelineStatus.VIDEO_GEN.value
        clip_paths = generate_clips(script)

        store[job_id]["status"] = PipelineStatus.VOICE.value
        commentary_path = generate_voice(script, job_id)

        store[job_id]["status"] = PipelineStatus.ASSEMBLY.value
        video_path = assemble_video(clip_paths, commentary_path, script, job_id)
        store[job_id]["video_path"] = video_path

        store[job_id]["status"] = PipelineStatus.THUMBNAIL.value
        thumbnail_path = generate_thumbnail(request, script, job_id)
        store[job_id]["thumbnail_path"] = thumbnail_path

        youtube_url = None
        if get_settings().youtube_upload_enabled:
            store[job_id]["status"] = PipelineStatus.UPLOAD.value
            youtube_url = upload_to_youtube(video_path, thumbnail_path, script)
            store[job_id]["youtube_url"] = youtube_url

        store[job_id]["status"] = PipelineStatus.COMPLETED.value
        return {
            "job_id": job_id,
            "status": PipelineStatus.COMPLETED.value,
            "video_path": video_path,
            "thumbnail_path": thumbnail_path,
            "youtube_url": youtube_url,
            "title": script.title,
            "description": script.description,
        }
    except Exception as e:
        store[job_id]["status"] = PipelineStatus.FAILED.value
        store[job_id]["error"] = str(e)
        raise
