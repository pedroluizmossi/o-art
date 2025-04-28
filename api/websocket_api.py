import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from comfy.comfy_core import get_queue

router = APIRouter(
    prefix="/websocket",
    tags=["websocket"],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "websocket",
    "description": "WebSocket endpoints for real-time updates.",
}

async def queue_status_updater(websocket: WebSocket, user_id: Optional[str] = None):
    await websocket.accept()
    last_queue = None
    try:
        while True:
            queue = await get_queue(user_id)
            if queue != last_queue:
                await websocket.send_json({"status": "success", "data": queue})
                last_queue = queue
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Cliente desconectado")
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})


@router.websocket("/queue-status")
async def websocket_endpoint(websocket: WebSocket, user_id: Optional[str] = None):
    """
    WebSocket endpoint to send queue status updates to the client.
    """
    await queue_status_updater(websocket, user_id)
