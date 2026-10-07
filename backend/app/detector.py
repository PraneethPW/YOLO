import threading
from pathlib import Path
from .config import settings
from .motion import MotionVerifier

class Detector:
    def __init__(self):
        self.models = {}
        self.verifiers = {}
        self.lock = threading.Lock()
        self.error = None
        self.runtime_configured = False

    def analyze(self, source_id, frame, timestamp):
        from ultralytics import YOLO
        import torch
        with self.lock:
            if not self.runtime_configured:
                torch.set_num_threads(2)
                self.runtime_configured = True
            if source_id not in self.models:
                # A separate tracker per source prevents track identity leaking between cameras.
                self.models[source_id] = YOLO(settings.yolo_model)
                self.verifiers[source_id] = MotionVerifier()
            result = self.models[source_id].track(frame, persist=True, tracker='bytetrack.yaml',
                classes=[2,3,5,7], conf=0.35, imgsz=640, verbose=False, device='cpu')[0]
            # Ultralytics device setup changes the thread count on first inference.
            # Keep subsequent inference within this service's two CPU allocation.
            torch.set_num_threads(2)
            tracks = []
            if result.boxes.id is not None:
                for box, identity, cls, confidence in zip(result.boxes.xyxy.cpu().tolist(),
                    result.boxes.id.cpu().tolist(), result.boxes.cls.cpu().tolist(), result.boxes.conf.cpu().tolist()):
                    tracks.append({'id': int(identity), 'box': [round(v,1) for v in box],
                                   'class': result.names[int(cls)], 'confidence': round(confidence,3)})
            candidates = self.verifiers[source_id].update(tracks, timestamp)
            annotated = result.plot()
            return tracks, candidates, annotated

    def reset(self, source_id):
        with self.lock:
            self.models.pop(source_id, None)
            self.verifiers.pop(source_id, None)

detector = Detector()
