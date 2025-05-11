
from fastapi import APIRouter, WebSocket

from handler.websocket_handler import preview_updater, queue_status_updater, user_access_token

router = APIRouter(
    prefix="/websocket",
    tags=["websocket"],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "websocket",
    "description": "WebSocket endpoints for real-time updates.",
}

@router.websocket("/queue-status")
async def websocket_endpoint(
        websocket: WebSocket
):
    """
    WebSocket endpoint to send queue status updates to the client.
    """
    user_id = await user_access_token(websocket)
    await queue_status_updater(websocket, user_id)


@router.websocket("/preview")
async def preview_endpoint(
        websocket: WebSocket
):
    """
    WebSocket endpoint to send preview updates to the client.
    """
    user_id = await user_access_token(websocket)
    await preview_updater(websocket, user_id)