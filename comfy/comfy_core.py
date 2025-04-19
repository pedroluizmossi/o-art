"""
This module provides functions to interact with ComfyUI server for image generation.
It uses websockets API to monitor prompt execution and downloads images using the /history endpoint.
"""

import asyncio
import time
import datetime
import websockets
import json
import urllib.request
import urllib.error
from urllib.parse import urlencode, quote
from typing import Dict, List, Any, Optional
from core.logging_core import setup_logger
from core.config_core import Config
from core.metric_core import InfluxDBWriter
logger = setup_logger(__name__)
# Initialize configuration
config_instance = Config()
comfyui_instance = config_instance.Comfyui(config_instance)
server_address = comfyui_instance.get_server_address()

# Initialize InfluxDB writer
metric = InfluxDBWriter()

async def ws_connect(user_id: str) -> websockets.WebSocketClientProtocol:
    """
    Establish a WebSocket connection to the ComfyUI server.

    Args:
        user_id (str): The client ID for the WebSocket connection

    Returns:
        websockets.WebSocketClientProtocol: The established WebSocket connection

    Raises:
        websockets.exceptions.WebSocketException: If connection fails
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")

    uri = f"ws://{server_address}/ws?clientId={quote(user_id)}"
    logger.info(f"Connecting to {uri}")

    try:
        websocket = await websockets.connect(uri)
        await asyncio.sleep(0.1)  # Allow some time for the WebSocket connection to stabilize
        return websocket
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"Failed to connect to WebSocket: {e}")
        raise

async def queue_prompt(prompt: Dict[str, Any], client_id: str) -> Dict[str, Any]:
    """
    Queue a prompt for processing by the ComfyUI server.

    Args:
        prompt (Dict[str, Any]): The prompt data to be processed
        client_id (str): The client ID for the prompt

    Returns:
        Dict[str, Any]: The server response containing the prompt_id

    Raises:
        urllib.error.URLError: If the HTTP request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    if not prompt or not client_id:
        raise ValueError("prompt and client_id cannot be empty")

    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')

    try:
        url = f"http://{server_address}/prompt"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.URLError as e:
        logger.error(f"Failed to queue prompt: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response: {e}")
        raise

async def get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    """
    Retrieve an image from the ComfyUI server.

    Args:
        filename (str): The name of the image file
        subfolder (str): The subfolder containing the image
        folder_type (str): The type of folder

    Returns:
        bytes: The image data

    Raises:
        urllib.error.URLError: If the HTTP request fails
    """
    if not filename:
        raise ValueError("filename cannot be empty")

    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urlencode(data)

    try:
        url = f"http://{server_address}/view?{url_values}"
        with urllib.request.urlopen(url) as response:
            return response.read()
    except urllib.error.URLError as e:
        logger.error(f"Failed to get image {filename}: {e}")
        raise

async def get_history(prompt_id: str) -> Dict[str, Any]:
    """
    Retrieve the history of a prompt execution from the ComfyUI server.

    Args:
        prompt_id (str): The ID of the prompt

    Returns:
        Dict[str, Any]: The history data for the prompt

    Raises:
        urllib.error.URLError: If the HTTP request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    if not prompt_id:
        raise ValueError("prompt_id cannot be empty")

    try:
        url = f"http://{server_address}/history/{prompt_id}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except urllib.error.URLError as e:
        logger.error(f"Failed to get history for prompt {prompt_id}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse history response: {e}")
        raise

async def get_images(ws: websockets.WebSocketClientProtocol, client_id: str, prompt: Dict[str, Any]) -> Dict[str, List[bytes]]:
    """
    Process a prompt and retrieve the generated images.

    Args:
        ws (websockets.WebSocketClientProtocol): WebSocket connection to the ComfyUI server
        client_id (str): The client ID for the prompt
        prompt (Dict[str, Any]): The prompt data to be processed

    Returns:
        Dict[str, List[bytes]]: Dictionary mapping node IDs to lists of image data

    Raises:
        ValueError: If input parameters are invalid
        websockets.exceptions.WebSocketException: If WebSocket communication fails
        json.JSONDecodeError: If response parsing fails
    """
    if not ws or not client_id or not prompt:
        raise ValueError("WebSocket, client_id, and prompt cannot be empty")

    try:
        # Queue the prompt and get the prompt ID
        prompt_response = await queue_prompt(prompt, client_id)
        prompt_id = prompt_response['prompt_id']
        output_images = {}

        # Wait for execution to complete
        logger.info(f"Waiting for prompt {prompt_id} execution to complete")
        while True:
            try:
                out = await ws.recv()
                if isinstance(out, str):
                    try:
                        message = json.loads(out)

                        if message.get('type') == 'executing':
                            data = message.get('data', {})
                            if data.get('node') is None and data.get('prompt_id') == prompt_id:
                                logger.info(f"Prompt {prompt_id} execution completed")
                                break  # Execution is done
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse WebSocket message: {e}")
                else:
                    # Binary data (previews)
                    # If you need to decode binary stream for latent previews:
                    # from io import BytesIO
                    # from PIL import Image
                    # bytesIO = BytesIO(out[8:])
                    # preview_image = Image.open(bytesIO)
                    continue
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error while waiting for execution: {e}")
                raise

        # Get history and extract images
        history_data = await get_history(prompt_id)
        if prompt_id not in history_data:
            logger.warning(f"Prompt ID {prompt_id} not found in history data")
            return {}

        history = history_data[prompt_id]

        # Process each output node
        for node_id in history.get('outputs', {}):
            node_output = history['outputs'][node_id]
            images_output = []

            if 'images' in node_output:
                for image in node_output['images']:
                    try:
                        image_data = await get_image(
                            image.get('filename', ''),
                            image.get('subfolder', ''),
                            image.get('type', '')
                        )
                        images_output.append(image_data)
                    except Exception as e:
                        logger.error(f"Failed to get image {image.get('filename', '')}: {e}")
                        # Continue with other images instead of failing completely

            output_images[node_id] = images_output

        return output_images
    except Exception as e:
        logger.error(f"Error in get_images: {e}")
        raise

async def get_queue(user_id: Optional[str] = None) -> Dict[str, int]:
    """
    Get information about the current queue status from the ComfyUI server.

    Args:
        user_id (Optional[str]): If provided, filter queue information for this specific user

    Returns:
        Dict[str, int]: Dictionary containing queue information:
            - queue_running: Number of running items
            - queue_pending: Number of pending items
            - queue_position: Position in queue for the specified user (0 if not in queue)

    Raises:
        urllib.error.URLError: If the HTTP request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    try:
        url = f"http://{server_address}/queue"
        logger.debug(f"Fetching queue information from {url}")

        with urllib.request.urlopen(url) as response:
            queue_data = json.loads(response.read())

        # Extract queue data with defaults
        queue_running = queue_data.get("queue_running", [])
        queue_pending = queue_data.get("queue_pending", [])

        try:
            queue_running = [
                item for item in queue_running
                if len(item) > 3 and isinstance(item[3], dict)
            ]
        except Exception as e:
            logger.warning(f"Error filtering running queue items: {e}")
            queue_running = []

        # Filter pending queue items
        try:
            # Get all position numbers, sorted
            queue_position_size = sorted([item[0] for item in queue_pending if len(item) > 0], reverse=False)

            # Get position numbers for pending items
            queue_position = [item[0] for item in queue_pending if len(item) > 0]
        except Exception as e:
            logger.warning(f"Error filtering pending queue items: {e}")
            queue_position = []
            queue_position_size = []

        # Calculate final values
        queue_running_len = len(queue_running)
        queue_pending_len = len(queue_pending)

        # Calculate user's position in queue
        user_queue_position = 0
        if user_id:
            for i, item in enumerate(queue_pending):
                if len(item) > 3 and isinstance(item[3], dict) and item[3].get("client_id") == user_id:
                    user_queue_position = i + 1
                    break


        result = {
            "queue_running": queue_running_len,
            "queue_pending": queue_pending_len,
            "queue_position": user_queue_position
        }
        return result

    except urllib.error.URLError as e:
        logger.error(f"Failed to get queue information: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse queue response: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_queue: {e}")
        raise

async def check_queue_task(user_id: Optional[str] = None):
    queue = await get_queue(user_id)
    metric.write_data(
        measurement="queue_status",
        tags={"user_id": user_id},
        fields={
            "queue_running": int(queue["queue_running"]),
            "queue_pending": int(queue["queue_pending"]),
            "queue_position": int(queue["queue_position"])
        }
    )
    logger.debug(f"Queue status: {queue}")

# Dentro de comfy/comfy_core.py

async def execute_workflow(user_id: str, job_id: str, workflow_dict: Dict[str, Any]) -> Optional[Dict[str, List[bytes]]]:
    """
    Conecta ao ComfyUI, executa um workflow específico e retorna os resultados.
    Usa o user_id para o client_id do WebSocket e job_id para rastreamento/logging.
    """
    client_id = f"{user_id}"
    logger.info(f"Executando workflow para client_id: {client_id}")

    ws = None
    try:
        ws = await ws_connect(client_id)
        images_output = await get_images(ws, client_id, workflow_dict)
        logger.info(f"Execução do workflow para {client_id} concluída.")
        return images_output
    except Exception as e:
        logger.error(f"Falha ao executar workflow para {client_id}: {e}")
        return None
    finally:
        if ws is not None:
            await ws.close()
            logger.info(f"Conexão WebSocket para {client_id} fechada.")

