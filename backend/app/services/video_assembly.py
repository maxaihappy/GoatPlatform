"""Stitch clips + commentary + optional scoreboard into final video."""
from pathlib import Path
from typing import List
from app.config import get_settings
from app.models import MatchupScript


class VideoAssembly:
    """Assemble clips and audio into final highlight video."""

    def __init__(self):
        self.settings = get_settings()
        self.output_dir = Path(self.settings.output_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble(
        self,
        clip_paths: List[str],
        commentary_audio_path: str,
        script: MatchupScript,
        output_filename: str = "goat_matchup.mp4",
    ) -> str:
        """Concatenate clips, set commentary as audio, write final file."""
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips,
        )

        clips = []
        for p in clip_paths:
            if not Path(p).exists():
                continue
            clip = VideoFileClip(p)
            clips.append(clip)

        if not clips:
            raise ValueError("No valid clips to assemble")

        final = concatenate_videoclips(clips)

        if Path(commentary_audio_path).exists():
            audio = AudioFileClip(commentary_audio_path)
            # Match audio length to video or trim
            if audio.duration > final.duration:
                audio = audio.subclipped(0, final.duration)
            final = final.with_audio(audio)

        out_path = str(self.output_dir / output_filename)
        final.write_videofile(
            out_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        final.close()
        return out_path
