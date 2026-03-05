# Why Frontend and Backend Are Separate (and When “All Together” Makes Sense)

## What each part does

| Part | What it does | Where it runs |
|------|----------------|---------------|
| **Frontend** | UI: matchup form, “Generate” button, job status, results. Calls the API and shows the response. | User’s browser (JavaScript); can be served as static files from a CDN. |
| **Backend** | API + pipeline: script generation (LLM), video clips, voice, assembly, thumbnail, YouTube upload. Holds secrets and does heavy work. | A server (e.g. Cloud Run): Python, FFmpeg, external APIs. |

So: the **frontend** is the face users see and interact with; the **backend** is the engine that does the work and talks to AI/storage/YouTube.

---

## Why we split them (architecture and solution design)

### 1. Different runtimes and dependencies

- **Frontend:** JavaScript/React. Runs in the browser. No direct access to file system, no Python, no FFmpeg.
- **Backend:** Python, MoviePy, FFmpeg, OpenAI SDK, ElevenLabs, etc. Needs a real OS and CPU/memory for video encoding and long-running jobs.

You can’t run the current pipeline “in the browser.” So by definition there must be a **server-side** component (the backend). The only design choice is whether the UI is:
- **Separate** (its own app that calls the backend over HTTP), or
- **Served by the same process** (e.g. one server that both serves the UI and runs the pipeline).

Splitting frontend and backend means: **UI = one artifact** (static or Node app), **pipeline = another** (Python service). That’s the split we have.

### 2. Security: secrets and sensitive work

- API keys (OpenAI, ElevenLabs, YouTube, etc.) must **never** live in the frontend. Browsers are public; anyone can read JS and network calls.
- The backend runs on a server you control, so secrets stay in env vars / Secret Manager and are only used server-side.

So from a **solution design** perspective: “where do secrets and trusted work run?” → **Backend.** “Where do we put the UI?” → **Frontend** (no secrets). That alone is a strong reason to have a backend that is logically (and usually deployably) separate from the frontend.

### 3. Scaling and cost

- **Frontend:** Often just static files (HTML/JS/CSS). Can be put on a CDN (Firebase Hosting, Cloud CDN). Serves millions of hits cheaply; no CPU per request.
- **Backend:** Does the expensive work (LLM calls, video encoding). You want to scale this by **usage** (e.g. Cloud Run: scale to zero when idle, pay per request).

If “everything” were one big server, you’d scale the whole thing (including the cheap static part) with the expensive part. **Separating them** lets you:
- Host the frontend for very little (or free),
- Scale and pay for the backend only when the pipeline runs.

So from an **architecture** perspective: frontend and backend have different **scaling and cost profiles**, so it’s natural to deploy them separately.

### 4. Clear API contract

- Backend exposes an **HTTP API** (e.g. `POST /api/matchup/run`, `GET /api/jobs/{id}`).
- Frontend is “any client” that talks to that API. You could later add a mobile app, CLI, or another web UI without changing the backend.

So the **split gives a clear boundary**: “everything behind the API” is the backend; “everything that calls the API and renders UI” is the frontend. That’s good for design and maintenance.

### 5. Different tech and release cycles

- Frontend: React/Next.js, CSS, UX changes, A/B tests — often change frequently.
- Backend: Python, pipeline logic, integrations, secrets — often more stable.

Splitting lets you deploy and iterate on the UI without redeploying the pipeline, and vice versa.

---

## Why not “all together”?

“All together” can mean different things.

### Option A: One deployment unit that does both UI and API

- **Possible:** e.g. one Node server that serves the Next.js app **and** implements the API in Node (Next.js API routes). But then the **pipeline** (script, video, voice, assembly, thumbnail, YouTube) would have to be rewritten in Node or run as a subprocess.
- **Reality:** The pipeline is Python (OpenAI, MoviePy, ElevenLabs, etc.). So you’d either:
  - Rewrite everything in Node (big effort, fewer libraries for video/ML), or
  - Keep Python as a separate process or service and have Node call it — which is again “frontend + backend,” just with the UI and a thin API in one process.
- **Conclusion:** For this solution, “all in one process” either means a huge rewrite or still two runtimes (Node + Python). So we keep a **dedicated Python backend** and a **frontend** that talks to it.

### Option B: One repo, one “app,” but two services when deployed

- You can have one repo and one “product” but still **deploy** two pieces: static frontend (or frontend container) + backend API. That’s still frontend + backend from an **architecture** perspective; they’re just in the same repo.
- We already have that: one repo, frontend folder + backend folder, deployed as two things (e.g. Firebase + Cloud Run).

### Option C: Backend serves the frontend (no separate frontend host)

- **Possible:** Backend (e.g. FastAPI) serves static files (the built Next.js export) and the API from the same service. So one URL, one deployment: e.g. `https://api.example.com/` = UI, `https://api.example.com/api/` = API.
- **Pros:** Single deployment, single domain, no CORS.
- **Cons:**  
  - Frontend and backend scale together (you can’t put the UI on a free CDN and scale only the API).  
  - Every UI change requires a backend deploy.  
  - Backend container/image is larger (static assets inside it).
- So: “all together” in **one service** is possible, but you give up the **cost and scaling benefits** of a separate frontend. For a small app it’s a valid choice; for our design we preferred **cheap/free frontend hosting** and **backend scaling to zero**.

---

## When “all together” does make sense

- **Very small or internal tools** where one server is simpler and cost is not a concern.
- **Monolith-first** teams that want one codebase and one deploy (e.g. backend serves static build + API).
- **No heavy backend** — e.g. if the “backend” were only a few serverless functions and no video/FFmpeg, you could do more “in one place” (e.g. Next.js API routes + Vercel). Our pipeline is too heavy and Python-centric for that.

---

## Summary

| Question | Answer |
|----------|--------|
| **Why do we need a frontend?** | To give users a UI (form, buttons, status, results). It runs in the browser and must not hold secrets. |
| **Why do we need a backend?** | To run the pipeline (Python, FFmpeg, LLM, voice, YouTube) and keep secrets and heavy work off the client. |
| **Why not all together?** | “All together” in one process would require either rewriting the pipeline in Node (not practical) or still running Python separately. One server for both UI and API is possible (backend serves static frontend) but we chose to separate so the frontend can be hosted cheaply (e.g. Firebase) and the backend can scale independently. |
| **From a solution design perspective** | Frontend = presentation and user interaction; backend = secure, scalable execution and integrations. The split gives clear boundaries, better security, and better cost/scaling behavior. |

So: we need **both** frontend and backend because they do different jobs (UI vs. pipeline) in different environments (browser vs. server). They *could* be deployed as one service (backend serving the frontend), but we **separate them** so we can host the frontend cheaply and scale the backend on its own.
