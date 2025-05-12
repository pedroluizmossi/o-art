import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

import websockets

from core.comfy.config import server_address
from core.comfy.exceptions import ComfyUIError
from core.logging_core import setup_logger
from utils.security_util import safe_urlopen

logger = setup_logger(__name__)

async def ws_connect(user_id: str) -> websockets.WebSocketClientProtocol:
    """Connect to ComfyUI WebSocket server"""
    uri = f"ws://{server_address}/ws?clientId={urllib.parse.quote(user_id)}"
    logger.info("Connecting to %s", uri)
    try:
        websocket = await asyncio.wait_for(websockets.connect(uri), timeout=10.0)
        await asyncio.sleep(0.1)
        return websocket
    except websockets.exceptions.WebSocketException as e:
        logger.error("WebSocket connection failed: %s", e)
        raise ComfyUIError(f"WebSocket connection failed: {e}") from e
    except asyncio.TimeoutError as e:
        logger.error("WebSocket connection timed out to %s", uri)
        raise ComfyUIError("WebSocket connection timed out") from e
    except Exception as e:
        logger.error("Unexpected error connecting to WebSocket: %s", e)
        raise ComfyUIError(f"Unexpected error connecting to WebSocket: {e}") from e


async def queue_prompt(prompt: dict[str, Any], client_id: str) -> dict[str, Any]:
    """Queue a prompt for processing by ComfyUI"""
    if not prompt or not client_id:
        raise ValueError("prompt and client_id cannot be empty")

    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    url = f"http://{server_address}/prompt"
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    try:
        with safe_urlopen(req, timeout=30.0) as response:
            response_body = response.read()
            return json.loads(response_body)
    except urllib.error.HTTPError as e:
        error_details = None
        try:
            error_body = e.read().decode("utf-8")
            error_details = json.loads(error_body)
            logger.error("HTTP Error %s when queuing prompt. Details: %s", e.code, error_details)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            logger.error("HTTP Error %s when queuing prompt. Could not read error body.", e.code)
        raise ComfyUIError(
            "Failed to queue prompt", status_code=e.code, details=error_details
        ) from e
    except urllib.error.URLError as e:
        logger.error("URL Error queuing prompt: %s", e.reason)
        raise ComfyUIError(f"URL Error queuing prompt: {e.reason}") from e
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse ComfyUI response: %s",
            response_body.decode("utf-8", errors="ignore"),
        )
        raise ComfyUIError(f"Failed to parse ComfyUI response: {e}") from e
    except asyncio.TimeoutError as e:
        logger.error("Timeout queuing prompt to %s", url)
        raise ComfyUIError("Timeout queuing prompt") from e
    except Exception as e:
        logger.error("Unexpected error queuing prompt: %s", e)
        raise ComfyUIError(f"Unexpected error queuing prompt: {e}") from e


async def get_history(prompt_id: str) -> dict[str, Any]:
    """Get execution history for a prompt"""
    if not prompt_id:
        raise ValueError("prompt_id cannot be empty")
    url = f"http://{server_address}/history/{prompt_id}"
    try:
        with safe_urlopen(url, timeout=30.0) as response:
            response_body = response.read()
            return json.loads(response_body)
    except urllib.error.HTTPError as e:
        logger.error("HTTP Error %s getting history for %s", e.code, prompt_id)
        raise ComfyUIError(f"Failed to get history for {prompt_id}",
                           status_code=e.code) from e
    except urllib.error.URLError as e:
        logger.error("URL Error getting history for %s: %s", prompt_id, e.reason)
        raise ComfyUIError(f"URL Error getting history for {prompt_id}: {e.reason}") from e
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse history response for %s: %s",
            prompt_id,
            response_body.decode("utf-8", errors="ignore"),
        )
        raise ComfyUIError(f"Failed to parse history response for {prompt_id}: {e}") from e
    except asyncio.TimeoutError as e:
        logger.error("Timeout getting history for %s from %s", prompt_id, url)
        raise ComfyUIError(f"Timeout getting history for {prompt_id}") from e
    except Exception as e:
        logger.error("Unexpected error getting history for %s: %s", prompt_id, e)
        raise ComfyUIError(f"Unexpected error getting history for {prompt_id}: {e}") from e


async def get_queue(user_id: Optional[str] = None) -> dict[str, int]:
    """
    Get information about the current queue status from the ComfyUI server.

    Args:
        user_id (Optional[str]): If provided, filter queue information for this specific user

    Returns:
        dict[str, int]: Dictionary containing queue information:
            - queue_running: Number of running items
            - queue_pending: Number of pending items
            - queue_position: Position in queue for the specified user (0 if not in queue)

    Raises:
        urllib.error.URLError: If the HTTP request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    try:
        url = f"http://{server_address}/queue"
        logger.debug("Fetching queue information from %s", url)

        with safe_urlopen(url) as response:
            queue_data = json.loads(response.read())

        # Extract queue data with defaults
        queue_running = queue_data.get("queue_running", [])
        queue_pending = queue_data.get("queue_pending", [])

        try:
            queue_running = [
                item for item in queue_running if len(item) > 3 and isinstance(item[3], dict)
            ]
        except Exception as e:
            logger.warning("Error filtering running queue items: %s", e)
            queue_running = []

        # Calculate final values
        queue_running_len = len(queue_running)
        queue_pending_len = len(queue_pending)

        # Calculate user's position in queue
        user_queue_position = 0
        if user_id:
            for i, item in enumerate(queue_pending):
                if (
                    len(item) > 3
                    and isinstance(item[3], dict)
                    and item[3].get("client_id") == user_id
                ):
                    user_queue_position = i + 1
                    break

        result = {
            "queue_running": queue_running_len,
            "queue_pending": queue_pending_len,
            "queue_position": user_queue_position,
        }
        return result

    except urllib.error.URLError as e:
        logger.error("Failed to get queue information: %s", e)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse queue response: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error in get_queue: %s", e)
        raise
