from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from fastapi import APIRouter, HTTPException, Response, Depends

from handler.image_handler import handle_generate_image

router = APIRouter(
    prefix="/image",
    tags=["image"],
)



@router.post("/generate")
async def generate(access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),):
    user_id = str(access_token_info["id"])
    image = await handle_generate_image(user_id)
    return Response(content=list(image.values())[0][0], media_type="image/png")