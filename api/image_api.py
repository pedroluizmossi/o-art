from fief_client import FiefAccessTokenInfo

from api.auth_api import auth
from comfy.comfy_core import get_queue, generate_image
from fastapi import APIRouter, HTTPException, Response, Depends

router = APIRouter(
    prefix="/image",
    tags=["image"],
)



@router.post("/generate")
async def generate(access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),):
    user_id = str(access_token_info["id"])
    queue = await get_queue(user_id)
    if queue["queue_position"] > 0:
        raise HTTPException(status_code=400, detail="You already have images in queue")
    image = await generate_image(user_id)

    return Response(content=list(image.values())[0][0], media_type="image/png")