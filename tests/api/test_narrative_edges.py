import json
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)


def test_narrative_detect_anchors_empty():
    r = client.post("/api/narrative/detect-anchors", json={"scenes": []})
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    assert body.get("total_anchors", 0) == 0


def test_narrative_detect_anchors_missing_fields():
    payload = {"scenes": [{"duration": 1.5}, {"duration": 2.0}]}
    r = client.post("/api/narrative/detect-anchors", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True


def test_narrative_detect_anchors_string_intensity():
    payload = {
        "scenes": [
            {"duration": 1.0, "sentiment_label": "POSITIVE", "sentiment_intensity": "0.9"}
        ]
    }
    r = client.post("/api/narrative/detect-anchors", json=payload)
    assert r.status_code == 200
    assert r.json().get("success") is True

