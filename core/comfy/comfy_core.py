"""
Main ComfyUI integration module
"""
from core.comfy.config import expire_old_previews_queue_time, metric, preview_queue, server_address
from core.comfy.connection import get_history, get_queue, queue_prompt, ws_connect
from core.comfy.exceptions import ComfyUIError
from core.comfy.images import get_image, get_images
from core.comfy.preview import (
    clear_user_preview_queue,
    export_preview_queue,
    get_preview_queue,
    preview_queue_cleanup,
)
from core.comfy.workflow import check_queue_task, execute_workflow
from core.logging_core import setup_logger

# Setup module logger
logger = setup_logger(__name__)

# Export all functionality from the modular components
__all__ = [
    # Exceptions
    'ComfyUIError',
    
    # Config
    'server_address',
    'metric',
    'preview_queue',
    'expire_old_previews_queue_time',
    
    # Connection
    'ws_connect',
    'queue_prompt',
    'get_history',
    'get_queue',
    
    # Images
    'get_image',
    'get_images',
    
    # Preview
    'export_preview_queue',
    'get_preview_queue',
    'clear_user_preview_queue',
    'preview_queue_cleanup',
    
    # Workflow
    'execute_workflow',
    'check_queue_task',
]