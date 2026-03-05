# GOAT Matchup Video Generator

Fully automated pipeline: **one matchup input → ready-to-publish YouTube video**.

- **Input**: e.g. "Prime Michael Jordan vs Prime LeBron James" (player names, setting, game format)
- **Output**: 3–6 minute highlight video, thumbnail, title + description, optional auto-upload to YouTube

## Architecture

```
User (Frontend) → Backend API → Pipeline
  → Script (LLM) → Clips (Runway/placeholder) → Voice (ElevenLabs) → Assembly (MoviePy) → Thumbnail (DALL·E) → YouTube
```

| Step | Component | Tech |
|------|------------|------|
| 1 | Matchup API | FastAPI |
| 2 | Script + play sequence | OpenAI GPT-4 |
| 3 | Video clips per play | Runway Gen-3 or placeholder (MoviePy) |
| 4 | Commentary audio | ElevenLabs or silent placeholder |
| 5 | Final video | MoviePy + FFmpeg |
| 6 | Thumbnail | DALL·E 3 or PIL placeholder |
| 7 | Upload | YouTube Data API v3 |

## Project layout

- **`backend/`** – Python FastAPI app, Prefect flow, and services (script, video, voice, assembly, thumbnail, YouTube).
- **`frontend/`** – Next.js app: matchup form and pipeline trigger (sync or async with job polling).

## Quick start

### 1. Backend (Python 3.10+)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# For local testing without API keys, set USE_MOCK_SCRIPT=true in .env
# For full script generation, set OPENAI_API_KEY
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional: set `ELEVENLABS_API_KEY` for real voice; leave unset for silent placeholder.  
Clips default to **placeholder** (solid color + text) unless you set `USE_PLACEHOLDER_CLIPS=false` and provide `RUNWAY_API_KEY`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use the form to submit a matchup; choose "Run in background" to get a job ID and poll for status.

### 3. Trigger pipeline

- **Sync**: `POST /api/matchup/run` with JSON body `{ "player1", "player2", "setting", "game_format" }` – runs to completion and returns result (can take several minutes with placeholders).
- **Async**: `POST /api/matchup/run-async` – returns `job_id` immediately; poll `GET /api/jobs/{job_id}` for status and outputs.

## Environment (backend)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (for script) | Script generation; also used for DALL·E thumbnail if set |
| `ELEVENLABS_API_KEY` | No | Voice; silent placeholder if missing |
| `ELEVENLABS_VOICE_ID` | No | Default voice ID |
| `USE_PLACEHOLDER_CLIPS` | No | `true` (default) = MoviePy placeholder clips |
| `RUNWAY_API_KEY` | No | For real AI clips when placeholders off |
| `YOUTUBE_UPLOAD_ENABLED` | No | Set to `1` to enable upload |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` | If upload | OAuth credentials |

## Scaling

- Replace in-memory job store with Redis/DB.
- Run Prefect worker and use `run_deployment` for true async jobs.
- Store clips and final video in S3/GCS; serve via CDN.
- Add Auth (e.g. NextAuth) and rate limits for production.

## Legal & compliance

Using AI to generate video or voice that depicts or refers to **real people** can raise **right of publicity**, **defamation**, **deepfake**, and **privacy** issues. See **[docs/LEGAL_AND_COMPLIANCE.md](docs/LEGAL_AND_COMPLIANCE.md)** for risk areas and mitigations (disclaimers, labeling, vendor ToS, recommended practices). This project includes in-app disclaimers and ensures titles/descriptions are labeled as AI-simulated; you are responsible for using it in compliance with applicable law and platform terms.

## License

MIT.
