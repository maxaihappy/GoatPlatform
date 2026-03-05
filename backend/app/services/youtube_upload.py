"""YouTube upload via Data API v3."""
from pathlib import Path
from typing import Optional, List
from app.config import get_settings
from app.models import MatchupScript


class YouTubeUploader:
    """Upload video and set title, description, thumbnail."""

    def __init__(self):
        self.settings = get_settings()

    def upload(
        self,
        video_path: str,
        thumbnail_path: Optional[str],
        script: MatchupScript,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Upload video to YouTube; return video URL. Requires OAuth credentials."""
        if not self.settings.youtube_upload_enabled or not all(
            [
                getattr(self.settings, "youtube_client_id", None),
                getattr(self.settings, "youtube_client_secret", None),
            ]
        ):
            raise RuntimeError(
                "YouTube upload is disabled or credentials not set. "
                "Set YOUTUBE_UPLOAD_ENABLED=1 and OAuth credentials."
            )

        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": self.settings.youtube_client_id,
                    "client_secret": self.settings.youtube_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                }
            },
            scopes=scopes,
        )
        creds = flow.run_local_server(port=0)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": script.title[:100],
                "description": script.description,
                "tags": tags or script.tags or ["NBA", "GOAT", "basketball"],
                "categoryId": "17",  # Sports
            },
            "status": {"privacyStatus": "public"},
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )
        response = request.execute()
        video_id = response["id"]

        if thumbnail_path and Path(thumbnail_path).exists():
            media_thumb = MediaFileUpload(thumbnail_path, mimetype="image/png")
            youtube.thumbnails().set(videoId=video_id, media_body=media_thumb).execute()

        return f"https://www.youtube.com/watch?v={video_id}"
