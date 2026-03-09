import hashlib
import hmac

from app.config import settings

LIMS_WEBHOOK_SECRET = "lims-webhook-secret"


def verify_lims_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        LIMS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


LIMS_FIELD_MAPPING = {
    "lims_sample_id": "external_id",
    "sample_name": "alias",
    "species": "organism",
    "extraction_method": "library_construction_protocol",
    "library_kit": "library_kit",
    "flowcell_id": "flowcell_id",
    "lane": "lane",
}
