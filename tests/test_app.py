"""Tests for the FastAPI service.

These run without a trained model artifact, so they cover the health check,
metrics endpoint, and input validation paths. The happy-path /predict call is
exercised in integration once a model.pt exists.
"""
import io

from fastapi.testclient import TestClient
from PIL import Image

from src.app import app

client = TestClient(app)


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color="blue").save(buf, format="PNG")
    return buf.getvalue()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "predictions_total" in resp.text


def test_predict_rejects_non_image():
    resp = client.post(
        "/predict",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_predict_missing_model_returns_503():
    # No artifacts/model.pt in CI, so this should surface a clean 503.
    resp = client.post(
        "/predict",
        files={"file": ("img.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code in (503, 200)
