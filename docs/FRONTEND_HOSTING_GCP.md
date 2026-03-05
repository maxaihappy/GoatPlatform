# Why Backend-Only First & Cheap Frontend Hosting on GCP

## Why we deployed only the backend initially

- **Separation of concerns** – API (Cloud Run) and frontend can scale and deploy independently.
- **One container first** – Backend is the critical path (pipeline, secrets); frontend is static or a second service.
- **Frontend needs the API URL** – Once the backend URL is fixed (e.g. Cloud Run), the frontend is configured to call it and can be hosted anywhere.

So: backend was deployed first to get a stable API URL; the frontend is deployed separately and points to that URL.

---

## Cheap frontend hosting options in the Google Cloud ecosystem

| Option | Cost (typical) | Best for |
|--------|-----------------|----------|
| **Firebase Hosting** | Free tier: 10 GB storage, 360 MB/day transfer. Then ~$0.026/GB. | Static/exported Next.js, SPAs. **Cheapest.** |
| **Cloud Run (frontend container)** | Free: 2M requests/month. Then pay-per-request (~$0.00002400/request + CPU/memory). | Full Next.js with SSR or when you want one container. |
| **Cloud Storage (GCS) only** | Storage ~$0.020/GB/mo; egress ~$0.12/GB. | Raw file hosting; **no HTTPS/custom URL** out of the box. |
| **GCS + Load Balancer (+ CDN)** | GCS + **LB ~$18+/mo** + egress (+ optional CDN). | Static with custom domain/HTTPS; **often more expensive** than Firebase for small sites. |
| **App Engine (standard)** | Free tier; then per instance-hour. | Legacy option; Cloud Run is usually simpler and cheaper. |

**Recommendation:** Use **Firebase Hosting** for the frontend – free tier is generous and cheapest. Use **Cloud Run** if you need a Node server. Use **GCS + LB** only if you already have a LB or need tight GCS/CDN control.

---

## Can we use Google Cloud Storage (object storage)? Is it cheaper?

**Yes, GCS is an option** for serving static frontend files (HTML, JS, CSS, assets). Whether it’s cheaper depends on how you expose it.

### GCS-only (bucket website)

- You can enable **static website** on a bucket and get a URL like:
  - `https://storage.googleapis.com/YOUR_BUCKET/index.html`  
  - or (legacy) `http://YOUR_BUCKET.storage.googleapis.com`
- **Cost:** Storage (~$0.020/GB/month) + egress (~$0.12/GB for first 1TB) – **very cheap** at small scale.
- **Limitations:**
  - No custom domain or clean URLs without extra pieces.
  - HTTPS for `storage.googleapis.com` works, but not for your own domain unless you put something in front.
  - No built-in CDN; no “nice” SPA fallback (e.g. `/route` → `index.html`) unless you add a layer.
- So: **cheap in $**, but **not a full “hosting” solution** like Firebase Hosting or Cloud Run.

### GCS + Load Balancer (and optional Cloud CDN)

- Put a **Global HTTP(S) Load Balancer** in front of a **GCS backend bucket** to get:
  - Custom domain, HTTPS, and (optionally) Cloud CDN.
- **Cost:**
  - GCS: storage + egress (same as above).
  - **Load Balancer:** roughly **~$18+/month** (forwarding rule + LB component) before traffic.
  - CDN: extra if you enable it.
- So for a **single small frontend**, the **LB’s fixed cost usually makes GCS + LB more expensive than Firebase Hosting** (which has a free tier and no LB).

### Cheaper or more expensive?

| Scenario | Cheaper | More expensive |
|----------|---------|----------------|
| **Small/low-traffic frontend** | Firebase Hosting (free tier) | GCS + Load Balancer (LB minimum ~$18/mo) |
| **Very high egress, already have LB** | GCS + LB + CDN (egress and CDN pricing) | Firebase (if you exceed free tier and compare $/GB) |
| **“Just want a URL and HTTPS”** | Firebase or Cloud Run | GCS + LB (setup + fixed LB cost) |

**Summary:**  
- **GCS alone** is cheap in $ but **not** a full replacement for “hosted frontend” (no custom domain/HTTPS/SPA routing out of the box).  
- **GCS + Load Balancer** gives a proper hosted static site but is **usually more expensive than Firebase** for one small app because of the LB’s minimum cost.

---

## GCS vs Cloud Run: pros and cons

| | **Google Cloud Storage (GCS)** | **Cloud Run** |
|--|--------------------------------|----------------|
| **What it is** | Object storage; you upload files (e.g. static export), serve them. | Runs a container (e.g. Next.js server); pay per request + CPU/memory. |
| **Cost model** | Storage + egress. No “per request” charge. **Needs LB for proper hosting** (~$18+/mo). | Per request + CPU/memory. Free tier 2M req/mo. No fixed monthly if you’re under free tier. |
| **Cheaper when** | You already have a LB and/or very high, predictable traffic (GCS + CDN egress can win). | Low or variable traffic (free tier, pay only when used). |
| **More expensive when** | You add a LB just for one small site (LB dominates cost). | High, steady traffic (always-on container or many requests). |
| **Pros** | Simple storage; durable; good for assets; can use CDN; no cold starts. | No LB needed; HTTPS + URL out of the box; can run SSR/API in same service; auto-scale to zero. |
| **Cons** | No “app server”; custom domain/HTTPS/SPA routing need LB (and config). LB has minimum cost. | Cold starts; per-request and CPU cost; must maintain a container. |
| **Best for frontend** | Static-only sites when you already use GCS + LB (or need strict control over storage/CDN). | Static or dynamic frontend when you want one platform, no LB, and optional SSR. |

**When to choose which**

- **Firebase Hosting** – Default choice for a **static** frontend: free tier, HTTPS, CDN, no LB.
- **Cloud Run** – When you want the frontend **as a container** on GCP, or need **SSR**, without managing a Load Balancer.
- **GCS** – When you’re already using GCS + LB for other reasons, or you want **object storage + CDN** and are okay with the **LB cost** and setup.

---

## Implemented in this repo

### Option A: Firebase Hosting (cheapest – recommended)

Static export of the Next.js app. Free tier: 10 GB storage, 360 MB/day.

```bash
cd frontend
npm ci
# Point to your Cloud Run backend
export NEXT_PUBLIC_API_URL=https://goat-platform-745118591625.us-central1.run.app
npm run build
npx firebase-tools deploy --only hosting --project festive-post-473500-c3
```

Your app will be at `https://festive-post-473500-c3.web.app` (or your custom domain).

### Option B: Cloud Run (frontend container)

Run the Next.js server on Cloud Run. Free tier: 2M requests/month; then pay-per-request.

```bash
cd frontend
gcloud run deploy goat-platform-frontend \
  --source . \
  --region us-central1 \
  --project festive-post-473500-c3 \
  --set-env-vars "NEXT_PUBLIC_API_URL=https://goat-platform-745118591625.us-central1.run.app" \
  --allow-unauthenticated
```

Build uses the Dockerfile (standalone output); Cloud Run will build and deploy.

### Option C: Google Cloud Storage (GCS) – static only

Use this if you want object storage and accept either **no custom domain** (GCS URL only) or **GCS + Load Balancer** (extra ~$18+/mo).

**1) GCS-only (no Load Balancer) – cheap, but basic URL**

```bash
# Create bucket (same project as your backend)
gcloud storage buckets create gs://goat-platform-frontend-YOUR_PROJECT_ID --location=us-central1 --project=festive-post-473500-c3

# Build static export (set API URL before building)
cd frontend
export NEXT_PUBLIC_API_URL=https://goat-platform-745118591625.us-central1.run.app
npm run build

# Make bucket public (or use IAM for private access)
gcloud storage buckets add-iam-policy-binding gs://goat-platform-frontend-YOUR_PROJECT_ID \
  --member=allUsers --role=roles/storage.objectViewer --project=festive-post-473500-c3

# Upload the static export
gcloud storage cp --recursive out/* gs://goat-platform-frontend-YOUR_PROJECT_ID/
```

Your app will be at:  
`https://storage.googleapis.com/goat-platform-frontend-YOUR_PROJECT_ID/index.html`  
(or the bucket’s website URL if you set the main page). No custom domain or pretty paths unless you add a Load Balancer.

**2) GCS + Load Balancer (custom domain, HTTPS)**

Configure a **Global HTTP(S) Load Balancer** with a **backend bucket** pointing at the same GCS bucket, and (optionally) Cloud CDN. This gives a proper URL and HTTPS but adds the LB’s **~$18+/month** minimum cost. See [GCP doc: Setting up a static website](https://cloud.google.com/storage/docs/hosting-static-website) and “Load balancer” setup.
