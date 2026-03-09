import pytest
from app.services.lims import verify_lims_signature, LIMS_FIELD_MAPPING
import hashlib
import hmac


def test_verify_signature_valid():
    payload = b'{"event": "sample_registered"}'
    expected = hmac.new(b"lims-webhook-secret", payload, hashlib.sha256).hexdigest()
    assert verify_lims_signature(payload, f"sha256={expected}") is True


def test_verify_signature_invalid():
    payload = b'{"event": "sample_registered"}'
    assert verify_lims_signature(payload, "sha256=wrong") is False


def test_field_mapping():
    assert LIMS_FIELD_MAPPING["lims_sample_id"] == "external_id"
    assert LIMS_FIELD_MAPPING["species"] == "organism"


@pytest.mark.asyncio
async def test_lims_webhook_sample_registered(client):
    response = await client.post("/api/v1/integrations/lims/webhook", json={
        "event": "sample_registered",
        "lims_sample_id": "LIMS-2026-0042",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "received"


@pytest.mark.asyncio
async def test_lims_webhook_sequencing_complete(client):
    response = await client.post("/api/v1/integrations/lims/webhook", json={
        "event": "sequencing_complete",
        "lims_run_id": "NV-20260306-001",
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_lims_webhook_missing_event(client):
    response = await client.post("/api/v1/integrations/lims/webhook", json={})
    assert response.status_code == 400
