from uuid import UUID, uuid4
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from fief_client import FiefAccessTokenInfo
from pydantic import BaseModel, Field

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.image_handler import handle_generate_image

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/image",
    tags=["image"],
)


class GenerateImageRequest(BaseModel):
    workflow_id: UUID = Field(
        ...,
        description="ID do workflow a ser utilizado para gerar a imagem.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parâmetros para preencher o workflow (ex: {'positive_prompt': 'gato astronauta', 'seed': 123})",
    )


@router.post("/generate")
async def generate(
    request_data: GenerateImageRequest,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    user_id = str(access_token_info["id"])
    job_id = str(uuid4())

    try:
        image_data = await handle_generate_image(
            user_id=user_id,
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
                detail="Falha ao gerar imagem ou workflow não produziu saída esperada.",
            )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request_data.workflow_id}' não encontrado.",
        )
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Parâmetro obrigatório '{e}' ausente para o workflow '{request_data.workflow_id}'.",
        )
    except Exception as e:
        logger.error(
            f"Erro inesperado ao gerar imagem para user {user_id} com workflow {request_data.workflow_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))
