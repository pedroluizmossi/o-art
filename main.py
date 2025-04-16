from fastapi import FastAPI, Response, HTTPException
from comfy.comfy_core import generate_image, get_queue
from utils.env_core import load_env_file
from utils.influx_core import write_data
from utils.config_core import Config

###Routes
from api.auth_api import router as auth_router
from api.webhook_api import router as webhook_router

load_env_file()
app = FastAPI()
app.include_router(auth_router)
app.include_router(webhook_router)

config = Config()
@app.post("/generate")
async def generate(user_id: str):
    write_data("generate", {"user_id": user_id}, {"status": "start"})
    queue = await get_queue(user_id)
    if queue["queue_running"] > 0 or queue["queue_position"] > 0:
        raise HTTPException(status_code=400, detail="You already have images in queue")
    image = await generate_image(user_id)

    return Response(content=list(image.values())[0][0], media_type="image/png")