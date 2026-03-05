"""Video clip generation: Runway API or placeholder clips for each play."""
import uuid
from pathlib import Path
from typing import List
from app.config import get_settings
from app.models import PlayItem, MatchupScript


class VideoGenerator:
    """Generate 5-8 second clips per play via Runway or placeholder."""

    def __init__(self):
        self.settings = get_settings()
        self.storage = Path(self.settings.storage_path) / "clips"
        self.storage.mkdir(parents=True, exist_ok=True)

    def generate_clips(self, script: MatchupScript) -> List[str]:
        """Generate one clip per play; return list of local file paths."""
        paths = []
        for play in script.plays:
            path = self._generate_one(play)
            paths.append(path)
        return paths

    def _generate_one(self, play: PlayItem) -> str:
        if self.settings.use_placeholder_clips or not self.settings.runway_api_key:
            return self._placeholder_clip(play)
        return self._runway_clip(play)

    def _placeholder_clip(self, play: PlayItem) -> str:
        """Create a placeholder clip (solid color + text) using MoviePy for testing."""
        from moviepy import ColorClip, TextClip, CompositeVideoClip
        clip = ColorClip(size=(1280, 720), color=(30, 30, 50), duration=6.0)
        try:
            txt = TextClip(
                f"Play {play.play_number}: {play.player}\n{play.action}",
                font_size=28,
                color="white",
            ).with_duration(6.0).with_position("center")
            clip = CompositeVideoClip([clip, txt])
        except Exception:
            pass
        out_path = str(self.storage / f"play_{play.play_number}_{uuid.uuid4().hex[:8]}.mp4")
        clip.write_videofile(out_path, fps=24, codec="libx264", audio=False, logger=None)
        clip.close()
        return out_path

    def _runway_clip(self, play: PlayItem) -> str:
        """Call Runway Gen-3 API (image-to-video or text-to-video) when key is set."""
        # Runway API: https://docs.runwayml.com/
        # Placeholder: save a placeholder and return path; real integration would poll job
        return self._placeholder_clip(play)
