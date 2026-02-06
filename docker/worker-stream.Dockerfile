# Stream Worker: 채널별 subprocess (ffmpeg/gst)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/ /app/app/
COPY legacy/requirements.txt /app/legacy/requirements.txt
RUN pip install --no-cache-dir -r /app/legacy/requirements.txt
ENV PYTHONPATH=/app
CMD ["python", "-m", "app.services.worker_stream.main"]
