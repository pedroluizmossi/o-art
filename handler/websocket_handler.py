import asyncio
from io import BytesIO
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image

from api.auth_api import base_fief
from comfy.comfy_core import get_preview_queue, get_queue
from core.logging_core import setup_logger

logger = setup_logger(__name__)

async def queue_status_updater(websocket: WebSocket, user_id: Optional[UUID] = None):
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
        logger.info("Disconnected")
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

async def preview_updater(websocket: WebSocket, user_id: Optional[UUID] = None):
    # Removed await websocket.accept() here
    last_preview = None
    try:
        while True:
            preview = await get_preview_queue(user_id)
            if preview != last_preview:
                if isinstance(preview, Image.Image):
                    buffer = BytesIO()
                    preview.save(buffer, format="JPEG")
                    buffer.seek(0)
                    await websocket.send_bytes(buffer.read())
                last_preview = preview
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("Disconnected")
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

async def user_acess_token(websocket: WebSocket):
    """
    Validate the access token from the WebSocket headers.
    """
    access_token_info = websocket.headers.get("access_token")
    if not access_token_info:
        await websocket.send_json({"status": "error", "message": "Missing access token"})
        await websocket.close(code=4000)
        return None
    try:
        access_token_info = base_fief.validate_access_token(access_token_info)
    except Exception:
        await websocket.send_json({"status": "error", "message": "Invalid access token"})
        await websocket.close(code=4000)
        return None
    user_id = access_token_info["id"]
    return user_id