from sqlmodel import Session

from comfy.comfy_core import get_queue, generate_image
from model.user_model import User
from uuid import UUID
from core.logging_core import setup_logger
from fastapi import HTTPException, status

logger = setup_logger(__name__)

async def handle_generate_image(user_id: str):
    queue = await get_queue(user_id)
    if queue["queue_position"] > 0:
        raise HTTPException(status_code=400, detail="You already have images in queue")
    image = await generate_image(user_id)
    if not image:
        raise HTTPException(status_code=400, detail="Error generating image")
    return image