# Vercel + Railway deployment

## Railway backend

1. Create a Railway project and backend service from `PraneethPW/YOLO` (branch `main`). Use `/backend` as its root directory. Build with the included `Dockerfile`. Set the service health check to `/api/health`, its timeout to 120 seconds, one replica, and disable sleeping. These settings live in Railway's service configuration. Legacy `railway.toml` configuration is deprecated by Railway and is not included.
2. Attach a **persistent volume mounted at `/data`** before processing footage. Place the backend near the Neon database; this deployment uses Virginia (`us-east4-eqdc4a`). Neon stores records; the volume stores original videos, evidence images, and latest camera frames. Without the volume, deploys lose those files.
3. Set server-only variables from `backend/.env.example`. Never put them in frontend build variables or GitHub source.
4. Generate a public Railway domain. Health check: `/api/health`.

Required variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Your Neon SSL connection string |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `OPENROUTER_MODEL` | `openrouter/free` |
| `JWT_SECRET` | At least 32 random characters |
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

The included `/api` proxy keeps refresh cookies on the frontend's origin. It forwards bearer headers and streams live events. Camera frames, video uploads, and original-video downloads go directly to Railway using bearer authorization, bypassing Vercel function payload limits. The runtime endpoint exposes only the public backend origin. Direct file transfers require the correct CORS origin.

The Content Security Policy permits connections to `*.up.railway.app`. If using a custom backend domain, add that exact origin to `connect-src` in `frontend/vercel.json`.

## First access

Open the production site and choose **Use my camera** or **Analyze a video**. A private visitor session is created automatically. Select a real video to start processing immediately, or explicitly enable your camera in its analysis view. No location is fabricated. Visitor sessions last two hours and permit three sources, uploads up to 25 MB, and two uploads per five minutes. Their footage, events, jobs, and incident records are isolated from other visitors and the staff workspace. Ending the session stops its camera lease and cancels queued or active video jobs.

For the shared staff workspace, select **Operator sign in**. Create the first administrator account with your name, email, and a password (12+ characters). No setup token is required. Visitor sessions do not consume first-administrator setup. Concurrent setup requests cannot create additional administrators. Subsequent operators require single-use invitations created in Settings. Administrators can configure allowlisted CCTV sources and responder destinations. Staff uploads permit up to the configured upload limit (100 MB by default). Coordinates are optional; map markers require actual latitude and longitude.

The application starts with empty operational data. It does not invent live cameras, accident detections, geographic locations, or sent alerts.

## Road network

Open Road network in the workspace, or select Place on map from a source card or analysis view. Select the source, click its actual capture location on the map, enter its road/area label, and save. You can enter coordinates manually or drag the placement pin. Go to my area requests device location only to center the map; it does not assign device coordinates to footage automatically. No location is inferred from an uploaded file.

Locations persist in Neon and source-change events update connected workspaces. Source markers use received-frame timestamps: live requires a frame within ten seconds, delayed means a camera session has no fresh frame, and idle means capture is stopped. The side panel displays the actual latest annotated frame, frame age, tracked-vehicle count, and links to its analysis view. Analysis and map links open separate tabs so browser-camera capture can continue while the map is open. Keep the capture tab open; remote CCTV capture runs on the backend. Active incident rings open evidence review; the Incidents filter provides a review queue. Resolved or dismissed decisions remove the active ring through live events. The map queries up to 500 active incidents and displays a plus sign when that cap is reached.

Coordinates identify the source capture location, including its incident records. This is coverage and incident monitoring, not vehicle GPS tracking or a third-party public traffic feed. Sources without coordinates remain actionable in the source list and placement queue. Visitor sessions retain their privacy boundaries.

## Connect a responder

The responder must supply an HTTPS webhook. Add its hostname to `WEBHOOK_ALLOWED_HOSTS`, then create the destination in Settings. Provide the same signing secret to your receiver.

The server sends JSON with `delivery_id`, `event`, and `incident` fields. It includes:

- `X-AccidentAlert-Signature: sha256=...`: HMAC SHA-256 of the exact raw request body, using your signing secret.
- `Idempotency-Key`: the stable delivery UUID. Deduplicate this key to handle at-least-once retries.

Return a 2xx only when the receiver has accepted the alert. Non-2xx responses and timeouts retry with exponential delays, up to five attempts. The UI displays actual delivery status and lets administrators retry failures. A 2xx means the receiver accepted the request; it does not mean an ambulance has been dispatched.

There are no default emergency recipients and no automatic call to 911, 112, police, or ambulance services.

## Operational limits

Three concurrent remote CCTV streams or three browser camera sessions are allowed. Browser capture sends at most two sampled frames per second, waiting for each actual result before sending the next. Annotated frames return directly with the inference response. The view displays received-frame age, actual analyzed rate, and capture-to-result latency. Camera leases expire after 60 seconds without a frame. Actual processing throughput depends on CPU capacity. The detector samples uploaded footage at approximately four frames per second of source time. It does not calculate physical speed without calibration. Camera credentials embedded in stream URLs are rejected; use an allowlisted camera relay when authentication is needed.

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
