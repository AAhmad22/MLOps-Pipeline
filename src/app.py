"""FastAPI inference service.

Exposes:
  GET  /health   -> liveness/readiness probe used by Kubernetes
  GET  /metrics  -> Prometheus metrics for monitoring
  POST /predict  -> image classification endpoint
"""
from __future__ import annotations

import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from src.config import settings
from src.predict import predict

app = FastAPI(
    title="Image Classifier API",
    description="An ML model served as a containerised, monitored microservice.",
    version="1.0.0",
)

# --- Prometheus metrics ----------------------------------------------------
PREDICTIONS = Counter(
    "predictions_total", "Total prediction requests", ["label", "status"]
)
LATENCY = Histogram(
    "prediction_latency_seconds", "Time spent processing a prediction"
)


@app.get("/health")
def health() -> dict:
    """Simple health check for Kubernetes liveness/readiness probes."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    """Expose metrics in Prometheus text format."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        PREDICTIONS.labels(label="none", status="bad_request").inc()
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    image_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        PREDICTIONS.labels(label="none", status="too_large").inc()
        raise HTTPException(status_code=413, detail="File too large.")

    start = time.perf_counter()
    try:
        result = predict(image_bytes)
    except FileNotFoundError:
        PREDICTIONS.labels(label="none", status="model_missing").inc()
        raise HTTPException(
            status_code=503,
            detail="Model artifact not found. Train and mount a model first.",
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean 500 to the client
        PREDICTIONS.labels(label="none", status="error").inc()
        raise HTTPException(status_code=500, detail=str(exc))

    LATENCY.observe(time.perf_counter() - start)
    PREDICTIONS.labels(label=result["label"], status="ok").inc()
    return JSONResponse(content=result)
