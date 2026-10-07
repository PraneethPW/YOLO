FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /app/models && python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
ENV DATA_DIR=/data PYTHONUNBUFFERED=1 YOLO_MODEL=/app/yolo11n.pt
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
