"""LLM-based matchup script and play sequence generator."""
import json
import re
from openai import OpenAI
from app.config import get_settings
from app.models import MatchupRequest, MatchupScript, PlayItem


def _mock_script(request: MatchupRequest) -> MatchupScript:
    """Hardcoded script for local testing without OpenAI."""
    return MatchupScript(
        title=f"Prime {request.player1} vs Prime {request.player2} – AI Simulated 1v1",
        description=f"AI-simulated GOAT matchup: {request.player1} vs {request.player2}. {request.setting}. {request.game_format}.",
        narrative_intro=f"Tonight we pit {request.player1} against {request.player2} in a hypothetical {request.game_format} on {request.setting}. Let's see who comes out on top.",
        plays=[
            PlayItem(play_number=1, player=request.player1, action="crossover then midrange jumper", commentary_snippet=f"{request.player1} with the crossover… pull-up jumper… good!", video_prompt=f"Prime {request.player1} crossover and midrange jumper, {request.setting}, cinematic broadcast, slow motion, realistic lighting"),
            PlayItem(play_number=2, player=request.player2, action="power drive and dunk", commentary_snippet=f"{request.player2} answers with a powerful drive to the rim!", video_prompt=f"Prime {request.player2} driving dunk, {request.setting}, cinematic broadcast, slow motion"),
            PlayItem(play_number=3, player=request.player1, action="fadeaway jumper", commentary_snippet=f"{request.player1} fadeaway… nothing but net.", video_prompt=f"Prime {request.player1} fadeaway jumper, {request.setting}, cinematic"),
        ],
        final_score_player1=21,
        final_score_player2=18,
        outro_text=f"Final: {request.player1} takes it 21-18. What a matchup!",
        tags=["NBA", "GOAT", "basketball"],
    )


SCRIPT_SYSTEM = """You are a sports scriptwriter for highlight videos. Generate a compelling game narrative and a sequence of plays for a hypothetical matchup video. Output must be valid JSON matching the exact schema given. Do not include markdown code fences."""

# Disclosure text required for compliance (fictional/simulated content)
DISCLOSURE_PHRASE = "AI Simulated"
DISCLOSURE_SUFFIX = " – Fictional simulation, not real footage or statements."


def _ensure_disclosure(script: MatchupScript) -> MatchupScript:
    """Ensure title and description include clear AI-simulation disclosure for legal/compliance."""
    title = script.title
    description = script.description
    if DISCLOSURE_PHRASE.lower() not in title.lower():
        title = f"{title.rstrip('.')}{DISCLOSURE_SUFFIX}"
    if DISCLOSURE_PHRASE.lower() not in description.lower():
        description = f"{description.rstrip('.')} This is fictional, AI-simulated content only."
    return MatchupScript(
        title=title,
        description=description,
        narrative_intro=script.narrative_intro,
        plays=script.plays,
        final_score_player1=script.final_score_player1,
        final_score_player2=script.final_score_player2,
        outro_text=script.outro_text,
        tags=script.tags,
    )


SCRIPT_USER_TEMPLATE = """Create a {game_format} matchup script between {player1} and {player2} in this setting: {setting}.

Requirements:
- This is for a FICTIONAL, AI-simulated highlight video only. Title and description MUST include the phrase "AI Simulated" or "Fictional simulation" so viewers know it is not real.
- Generate 12-16 distinct plays (mix of scoring, blocks, assists if applicable).
- Each play should have: play_number (1-based), player (exactly "{player1}" or "{player2}"), action (brief, e.g. "crossover then midrange jumper"), commentary_snippet (one short line for voice-over), video_prompt (detailed prompt for AI video: include player name, action, setting, style like "cinematic NBA broadcast, slow motion, realistic lighting").
- Final score should be close, e.g. 21-18 or 21-19.
- narrative_intro: 2-3 sentences setting the stage.
- outro_text: 1-2 sentences wrapping up and declaring the winner.

Output ONLY a single JSON object with this exact structure (no other text):
{{
  "title": "string",
  "description": "string (1-2 sentences for YouTube)",
  "narrative_intro": "string",
  "plays": [
    {{
      "play_number": 1,
      "player": "{player1}" or "{player2}",
      "action": "string",
      "commentary_snippet": "string",
      "video_prompt": "string (full prompt for video clip)"
    }}
  ],
  "final_score_player1": 21,
  "final_score_player2": 18,
  "outro_text": "string",
  "tags": ["NBA", "GOAT", "basketball", ...]
}}"""


class ScriptGenerator:
    """Generate matchup script and play sequence using an LLM."""

    def __init__(self):
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            key = get_settings().openai_api_key
            if not key:
                raise ValueError("OPENAI_API_KEY is required for script generation")
            self._client = OpenAI(api_key=key)
        return self._client

    def generate(self, request: MatchupRequest) -> MatchupScript:
        if get_settings().use_mock_script:
            return _mock_script(request)
        prompt = SCRIPT_USER_TEMPLATE.format(
            game_format=request.game_format,
            player1=request.player1,
            player2=request.player2,
            setting=request.setting,
        )
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code block if present
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```\s*$", "", text)
        data = json.loads(text)
        plays = [
            PlayItem(
                play_number=p["play_number"],
                player=p["player"],
                action=p["action"],
                commentary_snippet=p["commentary_snippet"],
                video_prompt=p["video_prompt"],
            )
            for p in data["plays"]
        ]
        script = MatchupScript(
            title=data["title"],
            description=data["description"],
            narrative_intro=data["narrative_intro"],
            plays=plays,
            final_score_player1=data["final_score_player1"],
            final_score_player2=data["final_score_player2"],
            outro_text=data["outro_text"],
            tags=data.get("tags", []),
        )
        return _ensure_disclosure(script)
