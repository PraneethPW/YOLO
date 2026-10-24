# Accident Alert architecture

Open [the interactive architecture](architecture.html?theme=dark) or [the complete upload workflow](upload-workflow.html?theme=dark). [The API inventory](api-reference.md) lists every registered GET, POST and PATCH endpoint with pinned source links.

The diagrams use committed source at `370128c5a54d6a3c4c940fba6b97e3adf0ee3059`. Runtime roles are grouped for readability: the API transport includes the browser client and Vercel proxy; the vision/video node includes OpenCV decoding, YOLO/ByteTrack inference, temporal verification, analytics writes and FFmpeg replay generation. Worker threads run inside the backend process. Database relationships appear in the architecture's Database relationships card; this is an architecture overview rather than a physical-column ERD.

Select nodes to open source references. The Flow menu contains five guided views. Use Live to animate traffic, F for Presentation Stage, and Export for image, SVG or WebM options. Motion communicates authored connections; it is not a captured production trace. The upload timeline shows operation order rather than measured latency and groups consumption of the already-open event stream after the worker's writes.

Both final HTML files passed Archify showcase validation, evidence verification, strict artifact checks and real Chrome browser checks. Current receipts are in `archify-evidence/architecture-review-3/` and `archify-evidence/workflow-review-3/`. Architecture captures are in `archify-evidence/architecture-visual/`; its 1440×900 dark and 2048×1320 light captures were visually inspected for label fit, route clarity and containment. The final architecture has no reported arrow crossings.

Only documentation artifacts were added. The application was not started, and no database was connected to or modified. Cloud deployment and live schema state were not verified. Current authentication code takes precedence over stale visitor/invitation instructions in DEPLOYMENT.md.
