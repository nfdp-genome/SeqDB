from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/lims/webhook")
async def lims_webhook(request: Request):
    body = await request.body()
    data = await request.json()

    event = data.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing event type")

    if event == "sample_registered":
        return {
            "status": "received",
            "event": event,
            "message": "Sample registration event queued for processing",
        }
    elif event == "library_prepared":
        return {
            "status": "received",
            "event": event,
            "message": "Library preparation event queued for processing",
        }
    elif event == "sequencing_complete":
        return {
            "status": "received",
            "event": event,
            "message": "Sequencing completion event queued for processing",
        }
    else:
        return {"status": "ignored", "event": event, "message": "Unknown event type"}
