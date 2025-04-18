from comfy.comfy_core import get_queue, generate_image
from main import app
from fastapi import APIRouter, HTTPException, Response

router = APIRouter(
    prefix="/image",
    tags=["image"],
)



@router.post("/generate")
async def generate(user_id: str):
    queue = await get_queue(user_id)
    if queue["queue_running"] > 0 or queue["queue_position"] > 0:
        raise HTTPException(status_code=400, detail="You already have images in queue")
    image = await generate_image(user_id)

    return Response(content=list(image.values())[0][0], media_type="image/png")