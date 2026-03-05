"""Voice commentary from script using ElevenLabs."""
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.models import MatchupScript


class VoiceGenerator:
    """Convert script narrative + play commentary into a single audio file."""

    def __init__(self):
        self.settings = get_settings()
        self.storage = Path(self.settings.storage_path) / "audio"
        self.storage.mkdir(parents=True, exist_ok=True)

    def generate(self, script: MatchupScript, output_path: Optional[str] = None) -> str:
        """Build full commentary text and synthesize to MP3; return path to audio file."""
        parts = [
            script.narrative_intro,
            *[p.commentary_snippet for p in script.plays],
            script.outro_text,
        ]
        text = " ".join(parts)
        path = output_path or str(self.storage / "commentary.mp3")

        if not self.settings.elevenlabs_api_key:
            return self._placeholder_audio(path, duration_sec=60)

        return self._elevenlabs_synthesize(text, path)

    def _placeholder_audio(self, path: str, duration_sec: float = 60) -> str:
        """Create silent placeholder when no ElevenLabs key."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        try:
            from moviepy import AudioClip
            import numpy as np
            def silence(_t):
                return np.array([0.0])
            clip = AudioClip(silence, duration=min(duration_sec, 30), fps=44100)
            clip.write_audiofile(path, fps=44100, logger=None)
            clip.close()
        except Exception:
            # Minimal WAV so assembly can attach (moviepy may still use it or skip)
            with open(path, "wb") as f:
                f.write(b"\x00" * 1024)
        return path

    def _elevenlabs_synthesize(self, text: str, path: str) -> str:
        """Call ElevenLabs API and save MP3."""
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        # voice_id: use a default sports-style voice; override via ELEVENLABS_VOICE_ID env if needed
        voice_id = getattr(self.settings, "elevenlabs_voice_id", None) or "JBFqnCBsd6RMkjVDRZzb"
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            if hasattr(audio, "read"):
                f.write(audio.read())
            elif isinstance(audio, bytes):
                f.write(audio)
            else:
                for chunk in audio:
                    f.write(chunk if isinstance(chunk, bytes) else chunk.read())
        return path
