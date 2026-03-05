"""Request/response and domain models for the GOAT matchup pipeline."""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStatus(str, Enum):
    PENDING = "pending"
    SCRIPT = "script"
    VIDEO_GEN = "video_gen"
    VOICE = "voice"
    ASSEMBLY = "assembly"
    THUMBNAIL = "thumbnail"
    UPLOAD = "upload"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchupRequest(BaseModel):
    """Input to trigger the pipeline."""

    player1: str = Field(..., description="First player name, e.g. Michael Jordan")
    player2: str = Field(..., description="Second player name, e.g. LeBron James")
    setting: str = Field(
        default="outdoor Chicago court",
        description="Setting for the matchup",
    )
    game_format: str = Field(
        default="1v1 to 21",
        description="Game format, e.g. 1v1 to 21",
    )


class PlayItem(BaseModel):
    """A single play in the script."""

    play_number: int
    player: str  # player1 or player2 name
    action: str  # e.g. "crossover → midrange jumper"
    commentary_snippet: str  # Short line for voice-over
    video_prompt: str  # Full prompt for video generation


class MatchupScript(BaseModel):
    """Full script from LLM: narrative + plays + metadata."""

    title: str
    description: str
    narrative_intro: str
    plays: List[PlayItem]
    final_score_player1: int
    final_score_player2: int
    outro_text: str
    tags: List[str] = Field(default_factory=list)


class PipelineJob(BaseModel):
    """Job record for a single pipeline run."""

    job_id: str
    request: MatchupRequest
    status: PipelineStatus = PipelineStatus.PENDING
    script: Optional[MatchupScript] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    youtube_url: Optional[str] = None
    error: Optional[str] = None
