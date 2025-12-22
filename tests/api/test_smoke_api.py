import json
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_narrative_detect_anchors_minimal():
    payload = {
        "scenes": [
            {"duration": 3.0, "sentiment_label": "NEUTRAL", "sentiment_intensity": 0.2},
            {"duration": 2.0, "sentiment_label": "POSITIVE", "sentiment_intensity": 0.6},
        ]
    }
    r = client.post("/api/narrative/detect-anchors", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True




def test_generate_route_exists_validation_only():
    r = client.post("/api/v1/generate", json={"foo": "bar"})
    assert r.status_code in (400, 422)
