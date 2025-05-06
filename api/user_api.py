
from fastapi import APIRouter, Depends, UploadFile
from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from handler.user_handler import get_user_by_id_handler, user_update_profile_image_url_handler

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

### tags_metadata -> resources/openapi_tags_metadata.py
router_metadata = {
    "name": "user",
    "description": "User endpoints.",
}

@router.get("/me")
async def get_me(
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated())  # noqa: B008
):
    user = await get_user_by_id_handler(access_token_info["id"])
    return user

@router.put("/me/profile_image")
async def update_profile_image(
    data: UploadFile,
    access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),  # noqa: B008
):
    user = await user_update_profile_image_url_handler(
        access_token_info["id"], data.file, data.filename
    )
    return user


