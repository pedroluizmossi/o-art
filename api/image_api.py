import uuid
from typing import Any, Dict

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
    workflow_name: str = Field(
        ..., description="Nome do arquivo do workflow (ex: flux_default.json)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parâmetros para preencher o workflow (ex: {'positive_prompt': 'gato astronauta', 'seed': 123})",
    )


@router.post("/generate")
async def generate(
    request_data: GenerateImageRequest,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    user_id = str(access_token_info["id"])
    job_id = str(uuid.uuid4())

    try:
        request_data.parameters["user_id"] = user_id
        request_data.parameters["job_id"] = job_id

        image_data = await handle_generate_image(
            user_id=user_id,
            job_id=job_id,
            workflow_name=request_data.workflow_name,
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
            detail=f"Workflow '{request_data.workflow_name}' não encontrado.",
        )
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Parâmetro obrigatório '{e}' ausente para o workflow '{request_data.workflow_name}'.",
        )
    except Exception as e:
        logger.error(
            f"Erro inesperado ao gerar imagem para user {user_id} com workflow {request_data.workflow_name}: {e}"
        )
        raise HTTPException(status_code=500, detail="Erro interno no servidor ao gerar imagem.")
