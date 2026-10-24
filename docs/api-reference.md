# Verified API inventory

Pinned source: `370128c5a54d6a3c4c940fba6b97e3adf0ee3059`. Static inspection only; no application or database was started.

| Method | Endpoint | Handler / source |
| --- | --- | --- |
| GET | `/api/health` | [`health`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L66-L69) |
| GET | `/api/auth/status` | [`setup_status`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L72-L74) |
| POST | `/api/auth/register` | [`register`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L87-L110) |
| POST | `/api/auth/login` | [`login`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L113-L120) |
| POST | `/api/auth/refresh` | [`refresh`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L123-L135) |
| POST | `/api/auth/logout` | [`logout`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L138-L149) |
| POST | `/api/auth/visitor` | [`visitor`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L152-L154) |
| GET | `/api/sources` | [`sources`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L160-L170) |
| GET | `/api/library/sources` | [`library_sources`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L173-L178) |
| POST | `/api/sources` | [`create_source`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L190-L206) |
| PATCH | `/api/sources/{identity}/location` | [`update_source_location`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L227-L241) |
| POST | `/api/sources/{identity}/start` | [`start_source`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L244-L264) |
| POST | `/api/sources/{identity}/stop` | [`stop_source`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L267-L277) |
| POST | `/api/sources/{identity}/archive` | [`archive_source`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L280-L288) |
| POST | `/api/sources/{identity}/frame` | [`webcam_frame`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L291-L313) |
| POST | `/api/sources/{identity}/upload` | [`upload`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L316-L352) |
| GET | `/api/jobs` | [`jobs`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L355-L364) |
| POST | `/api/jobs/{identity}/retry` | [`retry_job`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L367-L385) |
| GET | `/api/sources/{identity}/analytics` | [`source_analytics`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L392-L410) |
| POST | `/api/jobs/{identity}/analytics/start` | [`build_recording_analytics`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L413-L434) |
| POST | `/api/sources/{identity}/feedback` | [`submit_feedback`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L444-L458) |
| GET | `/api/testimonials` | [`public_testimonials`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L461-L463) |
| GET | `/api/feedback` | [`feedback_queue`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L466-L470) |
| PATCH | `/api/feedback/{identity}` | [`review_feedback`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L477-L487) |
| GET | `/api/incidents` | [`incidents`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L490-L497) |
| PATCH | `/api/incidents/{identity}` | [`update_incident`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L513-L532) |
| POST | `/api/incidents/{identity}/explain` | [`explain`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L535-L570) |
| GET | `/api/sources/{identity}/snapshot` | [`source_snapshot`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L573-L579) |
| GET | `/api/incidents/{identity}/snapshot` | [`incident_snapshot`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L582-L588) |
| GET | `/api/jobs/{identity}/video` | [`job_video`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L591-L598) |
| GET | `/api/jobs/{identity}/replay` | [`recorded_replay`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L612-L615) |
| GET | `/api/jobs/{identity}/replay/info` | [`recorded_replay_info`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L618-L621) |
| GET | `/api/library/jobs/{identity}/replay` | [`shared_replay`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L624-L627) |
| GET | `/api/library/jobs/{identity}/replay/info` | [`shared_replay_info`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L630-L633) |
| GET | `/api/library/sources/{identity}/snapshot` | [`shared_snapshot`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L636-L643) |
| POST | `/api/jobs/{identity}/replay/retry` | [`retry_recorded_replay`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L646-L665) |
| GET | `/api/stats` | [`stats`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L668-L683) |
| GET | `/api/events` | [`events`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L687-L708) |
| GET | `/api/settings` | [`get_settings`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L711-L722) |
| POST | `/api/alert-targets` | [`target`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L731-L737) |
| PATCH | `/api/alert-targets/{identity}` | [`toggle_target`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L744-L750) |
| GET | `/api/alerts` | [`alerts`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L753-L758) |
| POST | `/api/alerts/{identity}/retry` | [`retry_alert`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L761-L768) |
| GET | `/api/audit` | [`audit_log`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L771-L774) |
| GET | `/api/export` | [`export`](https://github.com/PraneethPW/YOLO/blob/370128c5a54d6a3c4c940fba6b97e3adf0ee3059/backend/app/main.py#L777-L790) |

Frontend transport: [`api.ts`](../frontend/src/api.ts), [`proxy.ts`](../frontend/api/proxy.ts), [`runtime.ts`](../frontend/api/runtime.ts).

The `/api/auth/visitor` endpoint exists but always returns 401. `invitations` exists in the SQL schema but no invitation API is registered. `DEPLOYMENT.md` contains stale visitor/invitation instructions; current code governs these diagrams.
