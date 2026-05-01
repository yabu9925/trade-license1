import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def submit_application() -> str:
    """Submit a fresh application and return its ID."""
    response = client.post("/api/v1/trade-licenses", json={
        "applicant_id": "applicant-001",
        "business_details": {
            "name": "Test Biz",
            "type": "Electronics",
            "address": "123 Main St",
            "capital": 1000.0,
            "activity_description": "Consumer electronics retail"
        },
        "documents": [{"file_name": "reg.pdf", "storage_uri": "s3://bucket/reg.pdf"}],
        "payment_transaction_id": "txn-001",
        "payment_amount": 500.0,
    })
    assert response.status_code == 201
    return response.json()["application_id"]


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Full happy-path: Submit → Review → Approve ────────────────────────────────

def test_full_workflow_happy_path():
    app_id = submit_application()

    # Reviewer accepts
    resp = client.post(f"/api/v1/trade-licenses/{app_id}/review", json={
        "reviewer_id": "reviewer-001",
        "action": "Accept",
        "note": "All good",
    })
    assert resp.status_code == 200

    # Approver approves
    resp = client.post(f"/api/v1/trade-licenses/{app_id}/approval", json={
        "approver_id": "approver-001",
        "action": "Approve",
        "note": "Compliant",
    })
    assert resp.status_code == 200

    # Verify final status
    resp = client.get(f"/api/v1/trade-licenses/{app_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Approved"


# ── Rereview loop ─────────────────────────────────────────────────────────────

def test_rereview_loop():
    app_id = submit_application()

    client.post(f"/api/v1/trade-licenses/{app_id}/review", json={
        "reviewer_id": "rev-1", "action": "Accept"
    })
    client.post(f"/api/v1/trade-licenses/{app_id}/approval", json={
        "approver_id": "appr-1", "action": "Rereview"
    })

    # Should be back in Rereview
    resp = client.get(f"/api/v1/trade-licenses/{app_id}")
    assert resp.json()["status"] == "Rereview"
    assert resp.json()["business_details"]["type"] == "Electronics"

    # Reviewer can review again
    resp = client.post(f"/api/v1/trade-licenses/{app_id}/review", json={
        "reviewer_id": "rev-1", "action": "Accept"
    })
    assert resp.status_code == 200


# ── Domain errors surface as 422 ─────────────────────────────────────────────

def test_cancel_by_wrong_applicant_returns_422():
    app_id = submit_application()
    resp = client.delete(f"/api/v1/trade-licenses/{app_id}?applicant_id=intruder-999")
    assert resp.status_code == 422


def test_approve_non_accepted_returns_422():
    app_id = submit_application()  # Still Pending
    resp = client.post(f"/api/v1/trade-licenses/{app_id}/approval", json={
        "approver_id": "appr-1", "action": "Approve"
    })
    assert resp.status_code == 422


# ── 404 for unknown application ───────────────────────────────────────────────

def test_get_unknown_application_returns_404():
    resp = client.get("/api/v1/trade-licenses/nonexistent-id")
    assert resp.status_code == 404
