# Inference Worker: AI 추론, ai.events 발행 (GPU 이미지로 교체 가능)
FROM python:3.11-slim
WORKDIR /app
COPY app/ /app/app/
COPY legacy/requirements.txt /app/legacy/requirements.txt
RUN pip install --no-cache-dir -r /app/legacy/requirements.txt
ENV PYTHONPATH=/app
CMD ["python", "-m", "app.services.worker_infer.main"]
