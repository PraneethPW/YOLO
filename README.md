# Accident Alert

A real road-video monitoring and incident-review application based on the supplied project deck. React, TypeScript, Tailwind, Framer Motion, and Three.js on the frontend. FastAPI, OpenCV, YOLO11, and ByteTrack on the backend. Neon PostgreSQL persists operational records. OpenRouter's free router explains measured evidence.

The application never seeds example cameras, incidents, locations, metrics, or alert deliveries. Connect a real source to populate the workspace.

## Implemented workflows

- Private two-hour visitor sessions: open a camera or upload a real video directly, with isolated footage and records.
- Dedicated analysis views with annotated frames, tracked vehicles, received-frame age, actual camera roundtrip latency, job progress, cancellation, and retry from the stored video.
- Persistent analysis graphs for each recording and live source: weighted vehicle presence and peak trends, observed vehicle types, vision timing, incident timeline, a time inspector linked to original playback, and measured-history CSV export. Live history retains 24 hours; recording history remains attached to its job. Older recordings can rebuild graphs from their saved original.
- Genuine post-analysis feedback with opt-in public display, administrator moderation, and a landing-page testimonial section. No sample quotes or ratings are seeded.
- One-time administrator setup, password hashing, short-lived access tokens, rotating HttpOnly refresh cookies, operator invitations, and role checks.
- Video upload, a durable processing queue, job progress, cancellation, restart recovery, vehicle tracking, and annotated frames.
- Browser-camera frame ingestion and allowlisted RTSP/HTTP CCTV monitoring.
- Temporal verification based on abrupt movement and vehicle-box overlap across several frames. Candidate evidence includes supporting-frame counts, an image, source location, and video timestamp.
- Operator confirmation, dismissal, resolution, notes, original-video playback, and CSV export.
- OpenRouter signal explanations using free models only. No footage or precise location is transmitted to the LLM.
- Signed webhook alerts, persistent delivery attempts, retries, destination controls, and audit history.
- Shared live event updates, source health, and a coverage board using actual latest footage, frame freshness, camera state, location editing, and incident review. Visitors see only their own coverage. Responsive layouts and reduced-motion support.
- Cinematic image parallax, a scroll-responsive Three.js background, and motion transitions throughout the workspace.

## Detection scope

The pretrained model detects vehicles. Accident candidates use **heuristics**, not a crash-trained classifier. A score of 80/100 is not an 80% probability of an accident. No accident benchmark accuracy is claimed. ByteTrack and pixel-space motion are most suitable for fixed cameras. Moving dashcams require camera-motion compensation or a separately trained temporal model before reliable autonomous confirmation.

Operators review candidates before confirmation. By default only confirmation queues an alert. `AUTO_ALERT_CANDIDATES=true` can explicitly enable unconfirmed candidate notifications, labeled with their actual status. Neither YOLO nor the LLM automatically contacts public emergency services. Delivery requires your configured webhook receiver. Integrating a real responder organization requires its endpoint and agreement to receive alerts.

## Local development

Use Node 22 or later, pnpm, and Python 3.11 or 3.12.

```sh
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL, OPENROUTER_API_KEY, and JWT_SECRET.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

In another terminal:

```sh
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:5173`. Choose **Use my camera** or **Analyze a video** to start a private visitor session. For a shared operations workspace, open **Operator sign in** and create the first administrator account with your name, email, and password. Once that account exists, new accounts require an invitation from Settings. No preset password exists in the source.

The application uses a dedicated `accident_alert` database schema. `DATABASE_SCHEMA` can change it. Each transaction sets its search path to support Neon transaction pooling.

## Hosting

See [DEPLOYMENT.md](DEPLOYMENT.md) for Railway, Vercel, persistent-volume setup, CORS configuration, first-account setup, and webhook verification. Keep one backend replica and one Uvicorn worker: in-process camera tracking belongs to that worker. CPU processing is bounded by actual hardware; processing latency is visible in the webcam view. Larger camera fleets need a separate inference-worker pool and object storage.

## Verification

```sh
cd frontend
pnpm build
cd ../backend
pytest tests -q
```

Additional integration checks during development use a separate temporary Neon schema and real video decoding. Production tables contain no verification fixtures.

## Source and assets

The landing image is original AI-generated artwork, used only as atmospheric artwork. It never appears as camera footage or incident evidence. Its prompt is documented in [ASSETS.md](ASSETS.md).

Ultralytics is distributed under AGPL-3.0 unless separately licensed. This project is AGPL-3.0, with the complete application source available. See [Ultralytics licensing](https://www.ultralytics.com/license).
