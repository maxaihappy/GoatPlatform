# How the Frontend Actually Works: Server vs Browser

## Short answers

1. **Does the frontend server send code to the browser and does it run in the browser?**  
   **Yes.** The server (or hosting) sends HTML, CSS, and JavaScript files. That code **runs in the user’s browser**.

2. **Where does computation happen?**  
   **In the browser.** Form state, button clicks, API calls (`fetch`), and React rendering all run on the user’s device.

3. **If it runs in the browser, why do we need a “frontend service”?**  
   Because the browser has to **get** the code from somewhere. The “frontend service” is just **hosting** — it stores the built files and delivers them when someone visits the URL. It doesn’t run your React app; it only **serves the files**. The app runs after the browser downloads those files.

---

## Step by step: what actually happens

### 1. Build (one-time, on your machine or in CI)

```text
npm run build   →   produces static files in out/
```

You get files like:

- `out/index.html`
- `out/_next/static/.../main-abc123.js`  (your React app)
- `out/_next/static/.../styles.css`

No server is “running” your app here. Build just **generates files**.

### 2. Hosting (the “frontend service”)

You put those files on a **host** — Firebase Hosting, Cloud Run, Nginx, etc. That host:

- **Stores** the files (on disk, in a bucket, in a container).
- **Sends** them over HTTP when a user asks for them.

So the “frontend service” is a **file server** (or CDN). It does almost no “computation” — it just responds with the right file for each URL (e.g. `/` → `index.html`, `/index.html` → same, `/static/...` → JS/CSS).

### 3. User opens the site (in the browser)

1. User goes to `https://your-app.web.app` (or your frontend URL).
2. The **host** (e.g. Firebase) returns `index.html`.
3. The browser reads `index.html`, sees `<script src="/_next/static/.../main.js">`, and **requests that JS file** from the same host.
4. The host returns the JS file (again, just “send this file”).
5. The **browser** loads and **executes** that JavaScript.

From this point on:

- **All “computation” is in the browser:** React runs there, form state lives there, “Generate” click is handled there.
- When the user clicks “Generate video,” the **browser** runs `fetch('https://your-api.run.app/api/matchup/run', { method: 'POST', body: ... })`. That request goes from the **user’s machine** directly to your **backend** (Cloud Run). The frontend host is not in the middle anymore; it already did its job by serving the HTML/JS/CSS.

So:

- **Frontend host** = serves static files (HTML, JS, CSS).
- **Backend** = receives API requests from the browser and runs the pipeline.
- **Browser** = runs the app and talks to the backend.

---

## Picture

```text
  [Build]
     │
     ▼
  Static files (index.html, main.js, styles.css)
     │
     ▼
  [Frontend “service” = Host]
  (Firebase / Cloud Run / any web server)
  - Only job: store files and send them when requested
  - No React execution here
     │
     │   User visits URL
     ▼
  [Browser]
  - Downloads index.html, main.js, CSS
  - Runs JavaScript (React, your UI logic)
  - User clicks “Generate” → browser sends fetch() to backend
     │
     │   HTTP POST /api/matchup/run
     ▼
  [Backend]
  - Runs pipeline (Python, FFmpeg, etc.)
  - Returns result to browser
```

So: the frontend “service” is not “running” your app. It’s **delivering** it. The app **runs in the browser**.

---

## Why we still need a “frontend service” (hosting)

- The browser can’t invent your HTML/JS. It has to load them from a URL.
- So **something** must listen at that URL and respond with the right files. That “something” is the frontend host (Firebase, Cloud Run, Nginx, etc.).
- That host can be extremely dumb: “for this path, return this file.” No business logic, no secrets, no pipeline — just **file delivery**. That’s why static hosting (Firebase, GCS, CDN) is cheap and simple.

If you had no frontend host, users would have no URL to open and no way to download your app. So we need a place to **serve** the frontend; we don’t need a “server that runs the frontend logic” — the browser does that.

---

## Summary table

| Question | Answer |
|----------|--------|
| Does the server send code to the browser? | Yes. It sends HTML, JS, and CSS files. |
| Where does that code run? | In the **browser**. |
| Where does computation happen (clicks, state, API calls)? | In the **browser**. |
| What does the “frontend service” do? | **Stores and serves** those files. It’s hosting/file delivery, not “running” your app. |
| Why do we need it? | So the browser has a URL to request the app from. Without it, there’s no way to get the files. |

So: **frontend service = file host**. **Frontend app = runs in the browser.** That’s why we need the “service” (hosting) even though all the real computation is in the browser.
