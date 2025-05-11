from typing import Any, Optional

from comfy.config import metric
from comfy.connection import get_queue, ws_connect
from comfy.exceptions import ComfyUIError
from comfy.images import get_images
from core.logging_core import setup_logger

logger = setup_logger(__name__)

async def execute_workflow(
    user_id: str, job_id: str, workflow_dict: dict[str, Any]
) -> Optional[dict[str, list[bytes]]]:
    """Execute a workflow on the ComfyUI server"""
    client_id = f"{user_id}"
    logger.info("Executing workflow for user %s (job: %s)", user_id, job_id)
    ws = None
    try:
        ws = await ws_connect(client_id)
        images_output = await get_images(ws, client_id, workflow_dict)
        logger.info("Workflow execution successful for user %s (job: %s)",
                    user_id, job_id)
        return images_output
    except ComfyUIError as e:
        logger.error("ComfyUI execution failed for user %s (job: %s): %s",
                     user_id, job_id, e)
        raise e
    except ValueError as e:
        logger.error(
            "Invalid input for workflow execution user %s (job: %s): %s",
            user_id,
            job_id,
            e,
        )
        raise e
    except Exception as e:
        logger.exception(
            "Unexpected error during workflow execution for user %s (job: %s): %s",
            user_id,
            job_id,
            e,
        )
        raise ComfyUIError(f"Unexpected error during workflow execution: {e}") from e
    finally:
        if ws is not None:
            await ws.close()
            logger.info("WebSocket connection closed for user %s (job: %s)",
                        user_id, job_id)


async def check_queue_task(user_id: Optional[str] = None):
    """Check queue status and record metrics"""
    queue = await get_queue(user_id)
    metric.write_data(
        measurement="queue_status",
        tags={"user_id": user_id},
        fields={
            "queue_running": int(queue["queue_running"]),
            "queue_pending": int(queue["queue_pending"]),
            "queue_position": int(queue["queue_position"]),
        },
    )
    logger.debug("Queue status: %s", queue)
