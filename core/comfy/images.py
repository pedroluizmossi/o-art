import asyncio
import urllib.error
import urllib.parse
from io import BytesIO
from typing import Any

import websockets
from PIL import Image
from pydantic.v1 import UUID4

from core.comfy.config import server_address
from core.comfy.connection import get_history, queue_prompt
from core.comfy.exceptions import ComfyUIError
from core.comfy.preview import export_preview_queue
from core.logging_core import setup_logger
from utils.security_util import safe_urlopen

logger = setup_logger(__name__)
WEBSOCKET_RECEIVE_TIMEOUT = 120.0

async def get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    """Get an image from the ComfyUI server"""
    if not filename:
        raise ValueError("filename cannot be empty")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    url = f"http://{server_address}/view?{url_values}"
    try:
        with safe_urlopen(url, timeout=240.0) as response:  # Longer timeout for download
            return response.read()

    except urllib.error.HTTPError as e:
        logger.error("HTTP Error %s getting image %s", e.code, filename)
        raise ComfyUIError(f"Failed to get image {filename}", status_code=e.code) from e
    except urllib.error.URLError as e:
        logger.error("URL Error getting image %s: %s", filename, e.reason)
        raise ComfyUIError(f"URL Error getting image {filename}: {e.reason}") from e
    except asyncio.TimeoutError as e:
        logger.error("Timeout getting image %s from %s", filename, url)
        raise ComfyUIError(f"Timeout getting image {filename}") from e
    except Exception as e:
        logger.error("Unexpected error getting image %s: %s", filename, e)
        raise ComfyUIError(f"Unexpected error getting image {filename}: {e}") from e

async def get_images(
    ws: websockets.WebSocketClientProtocol, client_id: str, prompt: dict[str, Any]
) -> dict[str, list[bytes]]:
    """Get generated images from ComfyUI after executing a prompt."""
    if not ws or not client_id or not prompt:
        raise ValueError("WebSocket, client_id, and prompt cannot be empty")
    prompt_id = None
    try:
        prompt_response = await queue_prompt(prompt, client_id)
        prompt_id = prompt_response.get("prompt_id")
        if not prompt_id:
            logger.error(
                "Invalid response when queuing prompt for %s: %s",
                client_id, prompt_response
            )
            raise ComfyUIError(
                "Invalid response from ComfyUI when queuing prompt (missing prompt_id)"
            )
        output_images = {}

        logger.info("Waiting for prompt %s execution (client: %s)", prompt_id, client_id)
        await _wait_for_prompt_execution(ws, client_id, prompt_id)

        history_data = await get_history(prompt_id)
        if prompt_id not in history_data:
            logger.warning("Prompt ID %s not found in history data.", prompt_id)
            return {}
        output_images = await _collect_output_images(history_data[prompt_id], prompt_id)
        if not output_images:
            logger.warning("No images found or retrieved in outputs for prompt %s", prompt_id)
        return output_images
    except ComfyUIError as e:
        logger.error("ComfyUI error for prompt %s: %s", prompt_id, e)
        raise e

async def _wait_for_prompt_execution(
    ws: websockets.WebSocketClientProtocol, client_id: str, prompt_id: str,
) -> None:
    while True:
        try:
            ws_message = await asyncio.wait_for(ws.recv(), timeout=WEBSOCKET_RECEIVE_TIMEOUT)
            if isinstance(ws_message, str):
                try:
                    import json
                    message = json.loads(ws_message)
                    if message.get("type") == "executing":
                        data = message.get("data", {})
                        if data.get("node") is None and data.get("prompt_id") == prompt_id:
                            logger.info("Prompt %s execution completed.", prompt_id)
                            break
                        elif data.get("prompt_id") == prompt_id:
                            logger.debug("Prompt %s executing node: %s",
                                         prompt_id,
                                         data.get("node"))
                    elif (
                        message.get("type") == "execution_error"
                        and message.get("data", {}).get("prompt_id") == prompt_id
                    ):
                        error_data = message.get("data")
                        logger.error(
                            "Execution error from ComfyUI for prompt %s: %s", prompt_id, error_data
                        )
                        raise ComfyUIError("ComfyUI reported execution error", details=error_data)
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON message from WebSocket: %s...",
                                   ws_message[:100])
                except ComfyUIError:
                    raise
                except Exception as inner_e:
                    logger.error("Error processing WebSocket message: %s", inner_e)
            else:
                bytesio = BytesIO(ws_message[8:])
                preview_image = Image.open(bytesio)
                user_id = UUID4(client_id)
                await export_preview_queue(user_id, preview_image)
                continue
        except asyncio.TimeoutError as e:
            logger.error("WebSocket receive timeout while waiting for prompt %s", prompt_id)
            raise ComfyUIError(f"WebSocket receive timeout for prompt {prompt_id}") from e
        except websockets.exceptions.ConnectionClosedOK as e:
            logger.warning("WebSocket connection closed ok while waiting for prompt %s", prompt_id)
            raise ComfyUIError(
                f"WebSocket connection closed while waiting for prompt {prompt_id}"
            ) from e
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(
                "WebSocket connection closed with error while waiting for prompt %s: %s",
                prompt_id, e
            )
            raise ComfyUIError(
                f"WebSocket connection closed unexpectedly for prompt {prompt_id}: {e}"
            ) from e

async def _collect_output_images(history: dict[str, Any], prompt_id: str) -> dict[str, list[bytes]]:
    outputs = history.get("outputs", {})
    logger.debug("Processing outputs for prompt %s: %s", prompt_id, list(outputs.keys()))
    output_images = {}
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            node_images = []
            for image_info in node_output["images"]:
                filename = image_info.get("filename")
                if not filename:
                    logger.warning(
                        "Node %s output missing filename for prompt %s", node_id, prompt_id
                    )
                    continue
                try:
                    image_data = await get_image(
                        filename,
                        image_info.get("subfolder", ""),
                        image_info.get("type", "output"),
                    )
                    node_images.append(image_data)
                    logger.debug(
                        "Successfully retrieved image %s for node %s (prompt %s)",
                        filename, node_id, prompt_id
                    )
                except ComfyUIError as e:
                    logger.error(
                        "Failed to get image %s for node %s (prompt %s): %s",
                        filename, node_id, prompt_id, e
                    )
                except Exception as e:
                    logger.error(
                        "Unexpected error getting image %s for node %s (prompt %s): %s",
                        filename, node_id, prompt_id, e
                    )
            if node_images:
                output_images[node_id] = node_images
    return output_images

