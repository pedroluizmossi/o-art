#This is an example that uses the websockets api to know when a prompt execution is done
#Once the prompt execution is done it downloads the images using the /history endpoint

import asyncio
import websockets #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
from urllib.parse import urlencode

from utils.config_core import Config

config_instance = Config()
comfyui_instance = config_instance.Comfyui(config_instance)
server_address = comfyui_instance.get_server_address()

async def ws_connect(user_id):
    uri = f"ws://{server_address}/ws?clientId={user_id}"
    print(f"Connecting to {uri}")
    websocket = await websockets.connect(uri)
    await asyncio.sleep(0.1)  # Allow some time for the WebSocket connection to stabilize
    return websocket

def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

async def get_images(ws, client_id, prompt):
    prompt_id = queue_prompt(prompt, client_id)['prompt_id']
    output_images = {}
    while True:
        out = await ws.recv()
        if isinstance(out, str):
            message = json.loads(out)

            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            # If you want to be able to decode the binary stream for latent previews, here is how you can do it:
            # bytesIO = BytesIO(out[8:])
            # preview_image = Image.open(bytesIO) # This is your preview in PIL image format, store it in a global
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

async def get_queue(user_id=None):
    with urllib.request.urlopen(f"http://{server_address}/queue") as response:
        queue_data = json.loads(response.read())
        queue_running = queue_data.get("queue_running", [])
        queue_pending = queue_data.get("queue_pending", [])
        queue_position = queue_data.get("queue_pending", [])
        queue_position_size = []
        if user_id is not None:
            try:
                queue_running = [item for item in queue_running if item[3]["client_id"] == user_id]
            except:
                queue_running = []
            try:
                queue_pending_user = [item for item in queue_pending if item[3]["client_id"] == user_id]
                queue_position_size = sorted([item[0] for item in queue_pending], reverse=False)
                queue_position = [item[0] for item in queue_pending_user]

            except:
                queue_position = []
                queue_position_size = []
        queue_running_len = len(queue_running)
        queue_pending_len = len(queue_pending)
        queue_position = queue_position_size.index(queue_position[0]) + 1 if queue_position else 0
        return {"queue_running": queue_running_len,
                "queue_pending": queue_pending_len,
                "queue_position": queue_position}


async def generate_image(user_id):
    prompt = json.loads(prompt_text)
    ws = await ws_connect(user_id)
    try:
        images = await get_images(ws, user_id, prompt)
    finally:
        await ws.close()

    return images

prompt_text = """
{
  "6": {
    "inputs": {
      "text": "mwv7_alpha_v01, A dinkfsn style ink wash painting, closeup portrait of stunning japanese woman, long loose hair, bangs, denim jacket, white blouse, leaning against a neon sign on a traditional Japanese street, night, neon signs, bokeh",
      "clip": [
        "44",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "13",
        0
      ],
      "vae": [
        "10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "10": {
    "inputs": {
      "vae_name": "FLUX1\\\\ae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "13": {
    "inputs": {
      "noise": [
        "25",
        0
      ],
      "guider": [
        "22",
        0
      ],
      "sampler": [
        "16",
        0
      ],
      "sigmas": [
        "17",
        0
      ],
      "latent_image": [
        "27",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "16": {
    "inputs": {
      "sampler_name": "dpmpp_2m"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "17": {
    "inputs": {
      "scheduler": "sgm_uniform",
      "steps": 30,
      "denoise": 1,
      "model": [
        "30",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "22": {
    "inputs": {
      "model": [
        "30",
        0
      ],
      "conditioning": [
        "26",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "BasicGuider"
    }
  },
  "25": {
    "inputs": {
      "noise_seed": 738250504518345
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "26": {
    "inputs": {
      "guidance": 3.5,
      "conditioning": [
        "6",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "FluxGuidance"
    }
  },
  "27": {
    "inputs": {
      "width": 768,
      "height": 1360,
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage",
    "_meta": {
      "title": "EmptySD3LatentImage"
    }
  },
  "30": {
    "inputs": {
      "max_shift": 1.15,
      "base_shift": 0.5,
      "width": 768,
      "height": 1360,
      "model": [
        "45",
        0
      ]
    },
    "class_type": "ModelSamplingFlux",
    "_meta": {
      "title": "ModelSamplingFlux"
    }
  },
  "44": {
    "inputs": {
      "model_type": "flux",
      "text_encoder1": "t5\\\\t5xxl_fp16.safetensors",
      "text_encoder2": "clip_l.safetensors",
      "t5_min_length": 512,
      "use_4bit_t5": "disable",
      "int4_model": "none"
    },
    "class_type": "NunchakuTextEncoderLoader",
    "_meta": {
      "title": "Nunchaku Text Encoder Loader"
    }
  },
  "45": {
    "inputs": {
      "model_path": "svdq-int4-flux-dev",
      "cache_threshold": 0,
      "attention": "nunchaku-fp16",
      "cpu_offload": "auto",
      "device_id": 0,
      "data_type": "bfloat16",
      "i2f_mode": "enabled"
    },
    "class_type": "NunchakuFluxDiTLoader",
    "_meta": {
      "title": "Nunchaku FLUX DiT Loader"
    }
  }
}
"""