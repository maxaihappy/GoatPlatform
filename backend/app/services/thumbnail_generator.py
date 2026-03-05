"""Thumbnail image generation (DALL-E or placeholder)."""
from pathlib import Path
from openai import OpenAI
from app.config import get_settings
from app.models import MatchupRequest, MatchupScript


class ThumbnailGenerator:
    """Generate thumbnail image for the matchup video."""

    def __init__(self):
        self.settings = get_settings()
        self.output_dir = Path(self.settings.output_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        request: MatchupRequest,
        script: MatchupScript,
        output_filename: str = "thumbnail.png",
    ) -> str:
        """Create thumbnail; return path to image file."""
        prompt = (
            f"Epic basketball poster, {request.player1} vs {request.player2}, "
            f"dramatic lighting, split composition, NBA arena background, "
            f"cinematic, high quality, no text"
        )
        out_path = str(self.output_dir / output_filename)

        if not self.settings.openai_api_key:
            self._placeholder_image(out_path)
            return out_path

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
            response_format="url",
        )
        import httpx
        url = getattr(response.data[0], "url", None)
        if not url and hasattr(response.data[0], "b64_json"):
            import base64
            Path(out_path).write_bytes(base64.b64decode(response.data[0].b64_json))
            return out_path
        if not url:
            self._placeholder_image(out_path)
            return out_path
        with httpx.Client() as http:
            r = http.get(url)
            r.raise_for_status()
            Path(out_path).write_bytes(r.content)
        return out_path

    def _placeholder_image(self, path: str) -> None:
        """Create a simple placeholder image (PIL) when no API key."""
        try:
            from PIL import Image
            img = Image.new("RGB", (1280, 720), color=(40, 40, 60))
            img.save(path)
        except ImportError:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG header
