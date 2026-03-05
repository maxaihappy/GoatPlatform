# What “Build” Means (Frontend vs Backend) and What `npm run` Is

## Do we build for frontend and backend?

**Yes, but in different ways:**

| Part    | What “build” means | Command / tool |
|---------|--------------------|----------------|
| **Frontend** | Turn your source code (React, TypeScript, CSS) into **optimized files** (HTML, JS, CSS) that the browser can load. | `npm run build` (runs Next.js build). |
| **Backend**  | There is **no separate “build” command** like the frontend. For deployment we **build a Docker image**: copy code, install Python dependencies, create a container. | `docker build` or `gcloud run deploy --source=backend` (which runs a Docker build under the hood). |

So:
- **Frontend:** “Build” = compile/bundle the app into static (or standalone) output.
- **Backend:** “Build” in our setup = **Docker image build** (package the app and its environment), not a compile step.

---

## What does `npm run` mean?

### `npm` = Node Package Manager

- Used for **JavaScript/Node** projects (like **pip** for Python).
- It installs dependencies (libraries) and runs scripts defined in **`package.json`**.

### `npm run <script-name>`

- **`npm run`** means: “Run one of the scripts defined in `package.json`.”
- In our frontend’s **`package.json`** we have:

```json
"scripts": {
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint"
}
```

So:

| You type        | What actually runs | What it does |
|-----------------|--------------------|--------------|
| `npm run dev`   | `next dev`         | Start Next.js **development** server (hot reload, local). |
| `npm run build` | `next build`       | **Build** the app: compile, bundle, optimize → output in `out/` or `.next/`. |
| `npm run start` | `next start`       | Start Next.js **production** server (serves the result of `build`). |
| `npm run lint`  | `next lint`        | Run the linter on the code. |

So **`npm run build`** = run the script named **`build`** in `package.json`, which is **`next build`**. That’s the **frontend** build.

- We **do not** use `npm run` for the **backend** (backend is Python; we use `pip`, `uvicorn`, and Docker).

---

## Frontend build in a bit more detail

When you run **`npm run build`** in the `frontend/` folder:

1. **Next.js** reads your app (e.g. `app/page.tsx`, `app/layout.tsx`, etc.).
2. It **compiles** TypeScript/JSX, **bundles** JavaScript, **processes** CSS (e.g. Tailwind).
3. It **optimizes** (minify, tree-shake) and writes the result to disk:
   - With **static export** (our default): **`out/`** — HTML + JS + CSS files you can host anywhere.
   - With **standalone** (Docker/Cloud Run): **`.next/standalone/`** — a Node server plus static assets.

So “build” for the frontend = **turn source into production-ready files (or a runnable server)**. No `npm run build` for the backend.

---

## Backend: no “npm run build,” but a “Docker build”

- The **backend** is **Python**. Python is interpreted; we don’t compile it to a binary.
- For **deployment** we “build” a **Docker image**:
  - Base image (e.g. `python:3.11-slim`).
  - Install system deps (e.g. `ffmpeg`) and Python deps (`pip install -r requirements.txt`).
  - Copy app code (`app/`, etc.).
  - Set the command to run the server (`uvicorn app.main:app ...`).

When we run **`gcloud run deploy --source=backend`**, Google Cloud **builds that Docker image** and then deploys it. So for the backend, “build” = **Docker image build**, not an `npm run build`-style step.

---

## Short summary

| Question | Answer |
|----------|--------|
| What does “build” mean for the **frontend**? | Run the frontend toolchain (Next.js) to produce optimized HTML/JS/CSS (e.g. in `out/` or `.next/`). Command: **`npm run build`**. |
| What does “build” mean for the **backend**? | Create a **Docker image** that contains Python, dependencies, and your code. Done by **Docker** / **Cloud Build** when you deploy (e.g. `gcloud run deploy --source=backend`). No `npm run build`. |
| What does **`npm run`** mean? | “Run a script from **`package.json`**.” Example: `npm run build` runs the script named `build` (which is `next build`). Only used in **Node/JS** projects (our frontend), not in the Python backend. |

So: we **build the frontend** with **`npm run build`**; we **build the backend** by **building a Docker image** when we deploy. “Build” = “prepare for production” in both cases, but the mechanism is different.
