import asyncio
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, List, Optional

import websockets

from core.config_core import Config
from core.logging_core import setup_logger
from core.metric_core import InfluxDBWriter
from utils.security_util import safe_urlopen

logger = setup_logger(__name__)
config_instance = Config()
server_address = config_instance.get("ComfyUI", "server", default="127.0.0.1:8188")

metric = InfluxDBWriter()

unsafe_ssl_context = ssl._create_unverified_context()


class ComfyUIError(Exception):
    """Custom exception for ComfyUI related errors."""

    def __init__(self, message, status_code=None, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

    def __str__(self):
        return f"ComfyUIError(status={self.status_code}): {super().__str__()} {self.details or ''}"


if not server_address:
    logger.critical("ComfyUI server address not configured.")
    raise ComfyUIError(
        "ComfyUI server address not configured. Did you forget to pay the server bill again?"
    )


async def ws_connect(user_id: str) -> websockets.WebSocketClientProtocol:
    uri = f"ws://{server_address}/ws?clientId={urllib.parse.quote(user_id)}"  # Usar urllib.parse
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
    except asyncio.TimeoutError:
        logger.error("Timeout queuing prompt to %s", url)
        raise ComfyUIError("Timeout queuing prompt")
    except Exception as e:
        logger.error("Unexpected error queuing prompt: %s", e)
        raise ComfyUIError(f"Unexpected error queuing prompt: {e}") from e


async def get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    if not filename:
        raise ValueError("filename cannot be empty")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    url = f"http://{server_address}/view?{url_values}"
    try:
        with safe_urlopen(url, timeout=240.0) as response:  # Timeout maior para download
            return response.read()

    except urllib.error.HTTPError as e:
        logger.error("HTTP Error %s getting image %s", e.code, filename)
        raise ComfyUIError(f"Failed to get image {filename}", status_code=e.code) from e
    except urllib.error.URLError as e:
        logger.error("URL Error getting image %s: %s", filename, e.reason)
        raise ComfyUIError(f"URL Error getting image {filename}: {e.reason}") from e
    except asyncio.TimeoutError:
        logger.error("Timeout getting image %s from %s", filename, url)
        raise ComfyUIError(f"Timeout getting image {filename}")
    except Exception as e:
        logger.error("Unexpected error getting image %s: %s", filename, e)
        raise ComfyUIError(f"Unexpected error getting image {filename}: {e}") from e


async def get_history(prompt_id: str) -> dict[str, Any]:
    if not prompt_id:
        raise ValueError("prompt_id cannot be empty")
    url = f"http://{server_address}/history/{prompt_id}"
    try:
        # context = unsafe_ssl_context # Descomente se precisar ignorar SSL
        # with urllib.request.urlopen(url, timeout=30.0, context=context) as response:
        with safe_urlopen(url, timeout=30.0) as response:
            response_body = response.read()
            return json.loads(response_body)
    except urllib.error.HTTPError as e:
        logger.error("HTTP Error %s getting history for %s", e.code, prompt_id)
        raise ComfyUIError(f"Failed to get history for {prompt_id}", status_code=e.code) from e
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
    except asyncio.TimeoutError:
        logger.error("Timeout getting history for %s from %s", prompt_id, url)
        raise ComfyUIError(f"Timeout getting history for {prompt_id}")
    except Exception as e:
        logger.error("Unexpected error getting history for %s: %s", prompt_id, e)
        raise ComfyUIError(f"Unexpected error getting history for {prompt_id}: {e}") from e


async def get_images(
    ws: websockets.WebSocketClientProtocol, client_id: str, prompt: dict[str, Any]
) -> dict[str, List[bytes]]:
    if not ws or not client_id or not prompt:
        raise ValueError("WebSocket, client_id, and prompt cannot be empty")

    prompt_id = None
    try:
        prompt_response = await queue_prompt(prompt, client_id)
        prompt_id = prompt_response.get("prompt_id")
        if not prompt_id:
            logger.error(
                "Invalid response when queuing prompt for %s: %s",
                client_id,
                prompt_response,
            )
            raise ComfyUIError(
                "Invalid response from ComfyUI when queuing prompt (missing prompt_id)"
            )

        output_images = {}
        logger.info("Waiting for prompt %s execution (client: %s)", prompt_id, client_id)

        while True:
            try:
                out = await asyncio.wait_for(ws.recv(), timeout=120.0)
                if isinstance(out, str):
                    try:
                        message = json.loads(out)
                        if message.get("type") == "executing":
                            data = message.get("data", {})
                            if data.get("node") is None and data.get("prompt_id") == prompt_id:
                                logger.info("Prompt %s execution completed.", prompt_id)
                                break
                            elif data.get("prompt_id") == prompt_id:
                                logger.debug(
                                    "Prompt %s executing node: %s",
                                    prompt_id,
                                    data.get("node"),
                                )
                        elif (
                            message.get("type") == "execution_error"
                            and message.get("data", {}).get("prompt_id") == prompt_id
                        ):
                            error_data = message.get("data")
                            logger.error(
                                "Execution error from ComfyUI for prompt %s: %s",
                                prompt_id,
                                error_data,
                            )
                            raise ComfyUIError(
                                "ComfyUI reported execution error", details=error_data
                            )
                    except json.JSONDecodeError:
                        logger.warning(
                            "Received non-JSON message from WebSocket: %s...", out[:100]
                        )  # Log truncado
                    except ComfyUIError:
                        raise
                    except Exception as inner_e:
                        logger.error("Error processing WebSocket message: %s", inner_e)

            except asyncio.TimeoutError:
                logger.error("WebSocket receive timeout while waiting for prompt %s", prompt_id)
                raise ComfyUIError(f"WebSocket receive timeout for prompt {prompt_id}")
            except websockets.exceptions.ConnectionClosedOK:
                logger.warning(
                    "WebSocket connection closed ok while waiting for prompt %s",
                    prompt_id,
                )
                raise ComfyUIError(
                    f"WebSocket connection closed while waiting for prompt {prompt_id}"
                )
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(
                    "WebSocket connection closed with error while waiting for prompt %s: %s",
                    prompt_id,
                    e,
                )
                raise ComfyUIError(
                    f"WebSocket connection closed unexpectedly for prompt {prompt_id}: {e}"
                ) from e

        history_data = await get_history(prompt_id)
        if prompt_id not in history_data:
            logger.warning("Prompt ID %s not found in history data.", prompt_id)
            return {}

        history = history_data[prompt_id]
        outputs = history.get("outputs", {})
        logger.debug("Processing outputs for prompt %s: %s", prompt_id, list(outputs.keys()))

        for node_id, node_output in outputs.items():
            if "images" in node_output:
                images_output = []
                for image_info in node_output["images"]:
                    filename = image_info.get("filename")
                    if not filename:
                        logger.warning(
                            "Node %s output missing filename for prompt %s",
                            node_id,
                            prompt_id,
                        )
                        continue
                    try:
                        image_data = await get_image(
                            filename,
                            image_info.get("subfolder", ""),
                            image_info.get("type", "output"),
                        )
                        images_output.append(image_data)
                        logger.debug(
                            "Successfully retrieved image %s for node %s (prompt %s)",
                            filename,
                            node_id,
                            prompt_id,
                        )
                    except ComfyUIError as e:  # Captura erros de get_image
                        logger.error(
                            "Failed to get image %s for node %s (prompt %s): %s",
                            filename,
                            node_id,
                            prompt_id,
                            e,
                        )
                    except Exception as e:
                        logger.error(
                            "Unexpected error getting image %s for node %s (prompt %s): %s",
                            filename,
                            node_id,
                            prompt_id,
                            e,
                        )

                if images_output:
                    output_images[node_id] = images_output

        if not output_images:
            logger.warning("No images found or retrieved in outputs for prompt %s", prompt_id)

        return output_images
    except ComfyUIError as e:
        logger.error("ComfyUI error for prompt %s: %s", prompt_id, e)
        raise e


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

        # Filter pending queue items
        try:
            # Get all position numbers, sorted
            queue_position_size = sorted(
                [item[0] for item in queue_pending if len(item) > 0], reverse=False
            )

            # Get position numbers for pending items
            queue_position = [item[0] for item in queue_pending if len(item) > 0]
        except Exception as e:
            logger.warning("Error filtering pending queue items: %s", e)
            queue_position = []
            queue_position_size = []

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


async def check_queue_task(user_id: Optional[str] = None):
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


async def execute_workflow(
    user_id: str, job_id: str, workflow_dict: dict[str, Any]
) -> Optional[dict[str, List[bytes]]]:
    client_id = f"{user_id}"
    logger.info("Executing workflow for user %s (job: %s)", user_id, job_id)
    ws = None
    try:
        ws = await ws_connect(client_id)
        images_output = await get_images(ws, client_id, workflow_dict)
        logger.info("Workflow execution successful for user %s (job: %s)", user_id, job_id)
        return images_output
    except ComfyUIError as e:
        logger.error("ComfyUI execution failed for user %s (job: %s): %s", user_id, job_id, e)
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
            logger.info("WebSocket connection closed for user %s (job: %s)", user_id, job_id)
