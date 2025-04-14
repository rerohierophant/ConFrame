#This is an example that uses the websockets api and the SaveImageWebsocket node to get images directly without
#them being saved to disk

import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        current_node = data['node']
        else:
            if current_node == 'save_image_websocket_node':
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output

    return output_images

prompt_text = """
{
        "1": {
            "inputs": {
            "image": "testproject2.png"
            },
            "class_type": "LoadImage",
            "_meta": {
            "title": "加载图像"
            }
        },
        "3": {
            "inputs": {
            "detail_method": "VITMatte",
            "detail_erode": 4,
            "detail_dilate": 2,
            "black_point": 0.01,
            "white_point": 0.99,
            "process_detail": False,
            "device": "cuda",
            "max_megapixels": 2,
            "image": [
                "1",
                0
            ],
            "birefnet_model": [
                "4",
                0
            ]
            },
            "class_type": "LayerMask: BiRefNetUltraV2",
            "_meta": {
            "title": "LayerMask: BiRefNet Ultra V2(Advance)"
            }
        },
        "4": {
            "inputs": {
            "model": "BiRefNet-general-epoch_244.pth"
            },
            "class_type": "LayerMask: LoadBiRefNetModel",
            "_meta": {
            "title": "LayerMask: Load BiRefNet Model(Advance)"
            }
        },
        "7": {
            "inputs": {
            "mask": [
                "11",
                0
            ]
            },
            "class_type": "MaskToImage",
            "_meta": {
            "title": "遮罩转换为图像"
            }
        },
        "11": {
            "inputs": {
            "mask": [
                "3",
                1
            ]
            },
            "class_type": "InvertMask",
            "_meta": {
            "title": "反转遮罩"
            }
        },
        "13": {
            "inputs": {
            "filename_prefix": "result",
            "images": [
                "7",
                0
            ]
            },
            "class_type": "SaveImage",
            "_meta": {
            "title": "保存图像"
            }
        }
        }
"""

prompt = json.loads(prompt_text)
#set the text prompt for our positive CLIPTextEncode
prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

#set the seed for our KSampler node
prompt["3"]["inputs"]["seed"] = 5

ws = websocket.WebSocket()
ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
images = get_images(ws, prompt)
ws.close() # for in case this example is used in an environment where it will be repeatedly called, like in a Gradio app. otherwise, you'll randomly receive connection timeouts
#Commented out code to display the output images:

for node_id in images:
    for image_data in images[node_id]:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_data))
        image.show()