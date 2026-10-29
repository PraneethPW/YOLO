# Shared live cameras and recorded datasets

Registered accounts can view two public Caltrans traffic cameras and five real recorded examples. Personal browser-camera capture remains available through **Use my camera**, followed by **Enable camera & start**. Camera selection is shown when more than one device is available. Browser camera capture stops when its page is closed.

## Live cameras

- I-5 at Pocket Road, Sacramento, California.
- I-5 at Florin Road, Sacramento, California.

The camera URLs and coordinates come from [Caltrans' District 3 CCTV catalog](https://cwwp2.dot.ca.gov/data/d3/cctv/cctvStatusD03.json), which is also used by [QuickMap](https://quickmap.dot.ca.gov/). The shared cards and source views show actual annotated frames, measured vehicle tracks, frame freshness, incident candidates and the rolling live analysis history. The backend samples approximately one frame per second per stream by default (`STREAM_SAMPLE_FPS=1`); this is a sampled analysis preview, not a claim of full-frame-rate inference. The public provider controls stream availability and any upstream delay.

Monitoring runs on the backend, reconnects with bounded backoff and resumes after application restarts. Operators can stop it; that choice is persisted. Registered members have read-only access to the shared cameras. Only explicitly allowlisted hosts may be connected; this deployment uses `CAMERA_ALLOWED_HOSTS=wzmedia.dot.ca.gov`.

The camera read timeout defaults to 30 seconds (`STREAM_READ_TIMEOUT_MS=30000`) to accommodate the provider's roughly 10–11 second HLS segments without reconnecting at each segment boundary.

## Recorded examples

| Recording | Provider and attribution |
| --- | --- |
| `car-detection.mp4` | [Intel IoT DevKit sample-videos](https://github.com/intel-iot-devkit/sample-videos), CC BY 4.0. |
| `person-bicycle-car-detection.mp4` | Intel IoT DevKit sample-videos, CC BY 4.0. |
| `vehicles.mp4` | [Roboflow Supervision demo assets](https://supervision.roboflow.com/0.28.0/assets/). |
| `vehicles-2.mp4` | Roboflow Supervision demo assets. |
| `motorway-a40.mp4` | “Motorway A40 – on bridge above the traffic,” Sounds of Changes, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Motorway_A40_-_on_bridge_above_the_traffic.webm), CC BY 3.0. The supplied [TrafficLens excerpt](https://github.com/safdar-hussain1/trafficlens/blob/main/web/public/clips/NOTICE.md) is shortened to 20 seconds, resized to 960×540, encoded as H.264 and has its audio removed. |

The original files stay in the persistent `/data` volume. Processing creates annotated H.264 replays and recorded track measurements. All five loop automatically when visible, with pause/restart controls and vehicle counts synchronized to playback. Recorded playback does not increase the live-camera count, create duplicate incidents or resend alerts. Offscreen playback is suspended to limit unnecessary transfers. YOLO annotations are modifications of the source footage. Credits appear on the source cards and detail pages.

The deployment restores the four matching public originals only after checking their frame counts against the saved records. Other missing recordings remain in the database and can be expanded under **Unavailable recording history**; their files are not fabricated.

## Explicit provisioning

The catalog is in `backend/app/catalog.json`. With production settings loaded and the persistent volume attached, run:

```sh
python -m app.provision_catalog
```

This downloads the five published examples, restores matching shared recordings or creates a deterministic new recording, and queues real analysis. It also configures the two shared live sources with monitoring enabled. Restart the application once after initial provisioning so the enabled cameras resume. Re-running the command preserves completed replays already on disk. It requires an existing administrator account and does not run automatically on each startup.
