# Stream Orchestrator: stream.commands 소비, lease 할당
FROM python:3.11-slim
WORKDIR /app
COPY app/ /app/app/
COPY legacy/requirements.txt /app/legacy/requirements.txt
RUN pip install --no-cache-dir -r /app/legacy/requirements.txt
ENV PYTHONPATH=/app
CMD ["python", "-m", "app.services.orchestrator.main"]
