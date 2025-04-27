import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from core.logging_core import setup_logger
from handler.model_handler import (
    get_all_models_handler,
    create_model_handler,
    get_model_by_id_handler,
    delete_model_handler,
    update_model_handler,
)
from model.model_model import Model, ModelUpdate, ModelCreate

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/model",
    tags=["model"],
)


@router.get("/", response_model=List[Model])
async def get_models(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Lists all available models.
    """
    return await get_all_models_handler()

@router.get("/{model_id}", response_model=Model)
async def get_model(
    model_id: uuid.UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Returns a specific model by its ID.
    """
    model = await get_model_by_id_handler(model_id)
    return model

@router.post("/", response_model=Model, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Creates a new model.
    """
    return await create_model_handler(model_data)

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: uuid.UUID,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Deletes a specific model by its ID.
    """
    await delete_model_handler(model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{model_id}", response_model=Model)
async def update_model(
    model_id: uuid.UUID,
    model_update_data: ModelUpdate,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    """
    Updates a specific model by its ID.
    """
    model = await update_model_handler(model_id, model_update_data)
    return model