from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from PIL import Image

from comfy.config import expire_old_previews_queue_time, metric, preview_queue
from comfy.exceptions import ComfyUIError
from core.logging_core import setup_logger

logger = setup_logger(__name__)

async def export_preview_queue(user_id: UUID, preview_image: Image.Image):
    """Add a preview image to the queue for a user"""
    try:
        metric.write_metric(
            measurement="preview_queue_cleanup",
            tags={},
            fields={"queue_size": preview_queue.qsize()},
        )
        await clear_user_preview_queue(user_id)
        await preview_queue.put(
            {
                "user_id": user_id,
                "image": preview_image,
                "timestamp": datetime.now(timezone.utc)
            }
        )
        logger.debug("Preview image added to queue, replacing previous images.")
    except Exception as e:
        logger.error("Error adding preview image to queue: %s", e)
        raise ComfyUIError(f"Error adding preview image to queue: {e}") from e

async def get_preview_queue(user_id: UUID) -> Optional[Image.Image]:
    """Get the latest preview image for a user"""
    try:
        preview_image = None
        queue_size = preview_queue.qsize()
        for _ in range(queue_size):
            item = await preview_queue.get()
            if (item["user_id"] == user_id and item["timestamp"] >
                    datetime.now(timezone.utc) - expire_old_previews_queue_time):
                preview_image = item["image"]
                await preview_queue.put(item)
                break
            else:
                await preview_queue.put(item)
        if preview_image:
            logger.debug("Latest preview image retrieved from queue for user %s.", user_id)
        return preview_image
    except Exception as e:
        logger.error("Error retrieving preview image from queue: %s", e)
        raise ComfyUIError(f"Error retrieving preview image from queue: {e}") from e

async def clear_user_preview_queue(user_id: UUID):
    """Remove all preview images for a user"""
    try:
        queue_size = preview_queue.qsize()
        for _ in range(queue_size):
            item = await preview_queue.get()
            if item["user_id"] != user_id:
                await preview_queue.put(item)
        logger.debug("Cleared preview queue for user %s.", user_id)
    except Exception as e:
        logger.error("Error clearing preview queue for user %s: %s", user_id, e)
        raise ComfyUIError(f"Error clearing preview queue for user {user_id}: {e}") from e

async def preview_queue_cleanup():
    """Remove expired preview images from the queue"""
    try:
        metric.write_metric(
            measurement="preview_queue_cleanup",
            tags={},
            fields={"queue_size": preview_queue.qsize()},
        )
        current_time = datetime.now(timezone.utc)
        items_to_keep = []
        while not preview_queue.empty():
            item = await preview_queue.get()
            logger.info(item)
            if current_time - item["timestamp"] > expire_old_previews_queue_time:
                logger.debug("Removing old preview image from queue.")
                continue
            items_to_keep.append(item)
        for item in items_to_keep:
            await preview_queue.put(item)
    except Exception as e:
        logger.error("Error during preview queue cleanup: %s", e)
        raise ComfyUIError(f"Error during preview queue cleanup: {e}") from e
