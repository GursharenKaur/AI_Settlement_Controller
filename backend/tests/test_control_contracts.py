from fastapi.testclient import TestClient

from app.main import app

from app.services import ai_investigation

client = TestClient(app, raise_server_exceptions=False)

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_control_summary_contract():
    response = client.get("/control/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_exceptions"] == 25

    assert data["action_required_count"] >= 0
    assert data["in_progress_count"] >= 0
    assert data["human_resolution_required_count"] >= 0
    assert data["monitor_count"] >= 0
    assert data["no_action_required_count"] >= 0

    assert (
        data["action_required_count"]
        + data["in_progress_count"]
        + data["human_resolution_required_count"]
        + data["monitor_count"]
        + data["no_action_required_count"]
        == data["total_exceptions"]
    )

    assert str(data["total_known_financial_impact"]) == "47300.00"
    assert data["highest_priority_payment_id"] == "2"
    assert data["highest_priority_score"] == 100
    assert data["outstanding_control_count"] >= 1
    
def test_risk_queue_contract():
    response = client.get("/risk/queue")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 25

    payment_ids = [item["payment_id"] for item in data]

    assert "2" in payment_ids

    payment_two = next(
        item for item in data
        if item["payment_id"] == "2"
    )

    assert payment_two["category"] == "MISSING_SETTLEMENT"
    assert payment_two["severity"] == "HIGH"
    assert str(payment_two["financial_impact"]) == "15000.00"
    assert payment_two["priority_score"] == 100
    assert payment_two["human_review_required"] is True

    assert payment_two["governance"]["governance_level"] == "HIGH"
    assert payment_two["governance"]["escalation_required"] is True

def test_governance_contract():
    response = client.get("/control/governance")

    assert response.status_code == 200

    data = response.json()

    payment_ids = [item["payment_id"] for item in data]

    assert "2" in payment_ids

    payment_two = next(
        item for item in data
        if item["payment_id"] == "2"
    )

    assert payment_two["governance"]["governance_level"] == "HIGH"
    assert payment_two["governance"]["escalation_required"] is True
    assert payment_two["remediation_status"] == "NOT_STARTED"
    assert payment_two["human_review_required"] is True

def test_payment_two_control_detail_contract():
    response = client.get("/control/exceptions/2/detail")

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == "2"
    assert data["category"] == "MISSING_SETTLEMENT"
    assert data["severity"] == "HIGH"
    assert str(data["financial_impact"]) == "15000.00"
    assert data["priority_score"] == 100
    assert data["remediation_status"] == "NOT_STARTED"
    assert data["human_review_required"] is True

    assert data["controlled_actions"] == []

    assert data["audit_events"] == []
def test_unknown_payment_returns_404():
    response = client.get("/exceptions/payment_that_does_not_exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_unknown_exception_lifecycle_returns_404():
    response = client.get(
        "/exceptions/payment_that_does_not_exist/lifecycle"
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "No exception lifecycle found for payment "
        "payment_that_does_not_exist"
    )


def test_unknown_controlled_action_returns_404():
    response = client.post("/controlled-actions/999999/execute")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Controlled action 999999 not found"
    )


def test_unknown_operational_exception_returns_404():
    response = client.get(
        "/control/exceptions/payment_that_does_not_exist"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No operational exception found for payment "
        "payment_that_does_not_exist"
    )


def test_unknown_operational_detail_returns_404():
    response = client.get(
        "/control/exceptions/payment_that_does_not_exist/detail"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No operational exception found for payment "
        "payment_that_does_not_exist"
    )


def test_unknown_payment_decision_returns_404():
    response = client.get(
        "/exceptions/payment_that_does_not_exist/decision"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Payment payment_that_does_not_exist not found"
    )

def test_unexpected_server_error_returns_500():
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/test-unexpected-error")
    def unexpected_error():
        raise RuntimeError("simulated internal failure")

    app.include_router(test_router)

    response = client.get("/test-unexpected-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error"
    }

def test_controlled_action_rejects_empty_payment_id():
    response = client.post(
        "/controlled-actions",
        json={
            "payment_id": "",
            "action_type": "INVESTIGATE_INVALID_STATE",
        },
    )

    assert response.status_code == 422


def test_controlled_action_rejects_oversized_payment_id():
    response = client.post(
        "/controlled-actions",
        json={
            "payment_id": "x" * 101,
            "action_type": "INVESTIGATE_INVALID_STATE",
        },
    )

    assert response.status_code == 422

def test_ai_investigation_failure_returns_503(monkeypatch):
    def failing_analysis(context):
        raise ai_investigation.AIInvestigationError(
            "simulated AI failure"
        )

    monkeypatch.setattr(
        "app.core.api.routes.intelligence.generate_investigation_analysis",
        failing_analysis,
    )

    response = client.get(
        "/intelligence/exceptions/2/investigation"
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI investigation service is temporarily unavailable"
    }

def test_request_logging_records_http_metadata(caplog):
    with caplog.at_level("INFO"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any(
        "HTTP request: GET /health -> 200" in record.message
        for record in caplog.records
    )