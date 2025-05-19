from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from fief_client import FiefAccessTokenInfo
from pydantic import BaseModel, Field

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.image_handler import (
    handle_generate_image,
)

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/image",
    tags=["image"],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "image",
    "description": "Image generation endpoints.",
}

class GenerateImageRequest(BaseModel):
    workflow_id: UUID = Field(
        ...,
        description="ID of the workflow to be used to generate the image.",
    )
    folder_id: UUID | None = Field(
        default=None,
        description="ID of the folder to save the image in. "
                    "If not provided, the image will not be saved.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to fill the workflow "
                    "(e.g.: {'positive_prompt': 'astronaut cat', 'seed': 123})",
    )


@router.post("/generate", description="Generate an image using a workflow. Only the first image will be returned.")
async def generate(
    request_data: GenerateImageRequest,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),  # noqa: B008
):
    user_id = access_token_info["id"]
    job_id = str(uuid4())
    folder_id = request_data.folder_id

    try:
        image_data = await handle_generate_image(
            user_id=user_id,
            folder_id=folder_id,
            job_id=job_id,
            workflow_id=request_data.workflow_id,
            params=request_data.parameters,
        )

        if image_data:
            first_node_id = next(iter(image_data))
            first_image_bytes = image_data[first_node_id][0]
            return Response(content=first_image_bytes, media_type="image/png")
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate image or workflow did not produce expected output.",
            ) from None
    except ValueError as err:
        logger.error(
            f"Value error while generating image for user {user_id} "
            f"with workflow {request_data.workflow_id}: {err}"
        )
        raise HTTPException(
            status_code=400,
            detail=str(err),
        ) from err
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request_data.workflow_id}' not found.",
        ) from err
    except KeyError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Required parameter '{err}' missing for workflow "
                   f"'{request_data.workflow_id}'.",
        ) from err
    except Exception as err:
        logger.error(
            f"Unexpected error while generating image for user {user_id} "
            f"with workflow {request_data.workflow_id}: {err}"
        )
        raise HTTPException(status_code=500, detail=str(err)) from err