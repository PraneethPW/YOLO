# Vercel + Railway deployment

## Railway backend

1. Create a Railway project and backend service from `PraneethPW/YOLO` (branch `main`). Use `/backend` as its root directory and `/backend/railway.toml` as its configuration path. Build with the included Dockerfile.
2. Attach a **persistent volume mounted at `/data`** before processing footage. Neon stores records; the volume stores original videos, evidence images, and latest camera frames. Without the volume, deploys lose those files.
3. Set server-only variables from `backend/.env.example`. Never put them in frontend build variables or GitHub source.
4. Generate a public Railway domain. Health check: `/api/health`.

Required variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Your Neon SSL connection string |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `OPENROUTER_MODEL` | `openrouter/free` |
| `JWT_SECRET` | At least 32 random characters |
| `BOOTSTRAP_TOKEN` | A separate random token, at least 24 characters |
| `COOKIE_SECURE` | `true` in production |
| `FRONTEND_ORIGINS` | Your exact Vercel production origin, without a trailing slash |
| `DATA_DIR` | `/data` |
| `YOLO_MODEL` | `/app/yolo11n.pt` (Docker default) |
| `MAX_UPLOAD_MB` | `100` (default) |
| `AUTO_ALERT_CANDIDATES` | `false` (default) |
| `CAMERA_ALLOWED_HOSTS` | Comma-separated exact camera hostnames, if connecting CCTV |
| `WEBHOOK_ALLOWED_HOSTS` | Comma-separated exact HTTPS alert destination hostnames |

The Docker build installs CPU PyTorch and downloads the actual YOLO weights. The first Docker build can take several minutes. Use one replica, one Uvicorn worker, and at least 2 GB RAM. Do not enable sleeping for continuous CCTV monitoring.

The CLI can deploy the `backend` directory with `railway up` once the project and service are linked. The repository workflow is preferable for automatic deploys after commits.

## Vercel frontend

1. Import `PraneethPW/YOLO` into Vercel. Set root directory to `frontend`. Choose Vite and pnpm. Build command: `pnpm build`. Output: `dist`.
2. Set **server-only** `BACKEND_URL` to the Railway HTTPS origin. No `VITE_` secret is needed.
3. Deploy, then set Railway `FRONTEND_ORIGINS` to that exact production Vercel origin. Add preview origins explicitly if you need them.

The included `/api` proxy keeps refresh cookies on the frontend's origin. It forwards bearer headers and streams live events. Video uploads and original-video downloads go directly to Railway using bearer authorization, bypassing Vercel function payload limits. The runtime endpoint exposes only the public backend origin. Direct file transfers require the correct CORS origin.

The Content Security Policy permits connections to `*.up.railway.app`. If using a custom backend domain, add that exact origin to `connect-src` in `frontend/vercel.json`.

## First access

Open the production site and select **Start monitoring**. Create the administrator account using the backend's `BOOTSTRAP_TOKEN`. Choose your own password (12+ characters). The setup token can create only the first account. Subsequent operators require single-use invitations created in Settings.

Connect an uploaded-video source or webcam. Enter actual road/location details. Coordinates are optional, but maps need both latitude and longitude. Video files may be MP4, MOV, AVI, WebM, or MKV up to the configured limit.

The application starts with empty operational data. It does not invent live cameras, accident detections, geographic locations, or sent alerts.

## Connect a responder

The responder must supply an HTTPS webhook. Add its hostname to `WEBHOOK_ALLOWED_HOSTS`, then create the destination in Settings. Provide the same signing secret to your receiver.

The server sends JSON with `delivery_id`, `event`, and `incident` fields. It includes:

- `X-AccidentAlert-Signature: sha256=...`: HMAC SHA-256 of the exact raw request body, using your signing secret.
- `Idempotency-Key`: the stable delivery UUID. Deduplicate this key to handle at-least-once retries.

Return a 2xx only when the receiver has accepted the alert. Non-2xx responses and timeouts retry with exponential delays, up to five attempts. The UI displays actual delivery status and lets administrators retry failures. A 2xx means the receiver accepted the request; it does not mean an ambulance has been dispatched.

There are no default emergency recipients and no automatic call to 911, 112, police, or ambulance services.

## Operational limits

Three concurrent remote CCTV streams or three browser camera sessions are allowed. Actual processing throughput depends on CPU capacity. The detector samples uploaded footage at approximately four frames per second of source time. It does not calculate physical speed without calibration. Camera credentials embedded in stream URLs are rejected; use an allowlisted camera relay when authentication is needed.

Store only footage you are authorized to process. Back up Neon and the `/data` volume. The supplied application has no automatic retention deletion; choose and implement a retention period appropriate to your deployment before building a large video archive. Rotate database and AI keys through the providers and update server variables when needed.

## Verify after deployment

- `/api/health` returns database `connected`.
- First-account setup, sign-in, sign-out, and refresh work.
- Uploaded footage progresses from queued to completed and produces an annotated frame.
- Browser camera processing reports actual received frames and tracked vehicles.
- Map markers appear only for sources with coordinates.
- A reviewed candidate records the operator decision.
- Your real responder receiver verifies signatures and returns the expected delivery result.

No real accident-detection accuracy, CCTV availability, responder delivery, or deployment success should be inferred from a successful frontend build alone.
