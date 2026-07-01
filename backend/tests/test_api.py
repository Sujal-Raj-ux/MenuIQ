"""FastAPI endpoint tests (deterministic routes; no OpenAI key required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_associations_returns_top_pairs():
    response = client.get("/associations?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["pairs"]) == 5

    top = data["pairs"][0]
    assert top["antecedent_name"]
    assert top["consequent_name"]
    assert top["lift"] >= 1.0

    # Planted answer key: Lobster Roll -> Onion Rings should rank highly.
    lobster_onion = [
        p
        for p in data["pairs"]
        if p["antecedent_name"] == "Lobster Roll"
        and p["consequent_name"] == "Onion Rings"
    ]
    assert lobster_onion
    assert 6.0 <= lobster_onion[0]["lift"] <= 6.6


def test_menu_matrix_returns_items():
    response = client.get("/menu-matrix")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 7
    burger = next(i for i in data["items"] if i["name"] == "Classic Burger")
    assert burger["quadrant"] == "Star"


def test_menu_analysis_requires_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.get("/menu-analysis")
    assert response.status_code == 503


def test_chat_requires_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 503


def test_api_key_skipped_when_unset(monkeypatch):
    """With API_KEY unset (dev), data routes stay open."""
    monkeypatch.delenv("API_KEY", raising=False)
    assert client.get("/menu-matrix").status_code == 200


def test_api_key_rejects_missing_key(monkeypatch):
    """With API_KEY set, requests without the header are rejected."""
    monkeypatch.setenv("API_KEY", "secret-test-key")
    assert client.get("/menu-matrix").status_code == 401


def test_api_key_accepts_valid_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-key")
    response = client.get("/menu-matrix", headers={"X-API-Key": "secret-test-key"})
    assert response.status_code == 200


UPLOAD_CSV = (
    "order_id,item_name,price,food_cost,category,quantity\n"
    "1,Latte,4,1,drink,2\n"
    "1,Croissant,3,1,bakery,1\n"
    "2,Latte,4,1,drink,1\n"
    "2,Bagel,3,1.5,bakery,1\n"
    "3,Croissant,3,1,bakery,2\n"
)


def _upload(csv: str = UPLOAD_CSV):
    return client.post(
        "/upload",
        files={"file": ("orders.csv", csv, "text/csv")},
    )


def test_upload_returns_summary_and_drives_analytics():
    response = _upload()
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    assert session_id
    assert data["distinct_items"] == 3
    assert data["orders"] == 3

    # The uploaded dataset (not the 7-item demo) should back this session.
    matrix = client.get(f"/menu-matrix?session_id={session_id}")
    assert matrix.status_code == 200
    items = matrix.json()["items"]
    assert {i["name"] for i in items} == {"Latte", "Croissant", "Bagel"}
    latte = next(i for i in items if i["name"] == "Latte")
    assert latte["units_sold"] == 3  # 2 + 1
    assert latte["margin"] == pytest.approx(3.0)

    assoc = client.get(f"/associations?session_id={session_id}")
    assert assoc.status_code == 200


def test_upload_without_session_keeps_demo_data():
    # Default route still serves the 7-item demo dataset.
    assert len(client.get("/menu-matrix").json()["items"]) == 7


def test_upload_rejects_file_missing_cost():
    bad = "order_id,item_name,price\n1,Latte,4\n2,Bagel,3\n"
    response = _upload(bad)
    assert response.status_code == 422


def test_unknown_session_falls_back_to_demo():
    response = client.get("/menu-matrix?session_id=upload-doesnotexist")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 7
