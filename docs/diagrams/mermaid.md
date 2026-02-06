flowchart LR
  C[Client/Player] -->|REST| G[API Gateway]
  G --> DB[(Control DB)]
  G -->|publish| K[(Kafka: stream.commands)]

  K --> O[Stream Orchestrator]
  O --> DB
  O -->|assign + lease| DB
  O -->|dispatch| W[Stream Worker Pool]

  W -->|spawn per channel| P[(ffmpeg/gst subprocess)]
  P --> OUT[(HLS Segments / RTSP Relay)]
  C -->|play| OUT

  W -->|optional frames| IQ[(Kafka/Redis: inference.requests)]
  IQ --> IW[Inference Worker Pool]
  IW -->|results| IR[(inference.results)]
  IR --> W

  W -->|events| KE[(Kafka: stream.events)]
  KE --> DB
  W --> M[Prometheus/Logs/Tracing]
  G --> M
  O --> M
