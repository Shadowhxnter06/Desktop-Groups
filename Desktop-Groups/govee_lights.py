import requests
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# These are defined once at the top so every function below can use them.
DOMAIN = "https://openapi.api.govee.com"
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY")

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Govee-API-Key": GOVEE_API_KEY
}


# ---------------------------------------------------------------------------
# DEVICE DISCOVERY
# ---------------------------------------------------------------------------

def get_govee_lights():

#    Fetches all devices linked to your Govee account, along with their sku and mac address.
    
    endpoint = "/router/api/v1/user/devices"

    response = requests.get(url=DOMAIN + endpoint, headers=HEADERS)
    response.raise_for_status()
    all_data = response.json()

    # Pull the three fields from each device entry
    govee_lights = []
    for device in all_data["data"]:
        govee_lights.append({
            "d_name":     device["deviceName"],
            "d_sku":      device["sku"],
            "d_mac_addr": device["device"]
        })

    return govee_lights


# ---------------------------------------------------------------------------
# SCENE DISCOVERY
# A "scene" is a pre-built lighting effect (e.g. "Lava Flow", "Ocean").
# Each scene has a paramId and an id — both are needed to activate it.
#
# There are two types:
#   - Built-in scenes: come with the device, found in the Govee app's "Scenes" tab.
#   - DIY scenes: ones you created yourself, found in the "DIY" tab.\
# ---------------------------------------------------------------------------

def get_govee_device_scenes(d_sku, d_mac_addr):

#    Returns all built-in scenes available for a device.

    endpoint = "/router/api/v1/device/scenes"
    data = {
        "requestId": str(uuid.uuid4()), 
        "payload": {
            "sku": d_sku,
            "device": d_mac_addr
        }
    }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    response.raise_for_status()
    return response.json()


def get_govee_device_diy_scenes(d_sku, d_mac_addr):
  
#   Returns all DIY scenes you've created for a device (the "DIY" tab in the app).

    endpoint = "/router/api/v1/device/diy-scenes"
    data = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": d_sku,
            "device": d_mac_addr
        }
    }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# DEVICE CONTROL
# ---------------------------------------------------------------------------

def toggle_govee_device_power(d_sku, d_mac_addr, toggle):
    
#   Turns a device on or off.

    if toggle == "off":
        toggle_value = 0
    elif toggle == "on":
        toggle_value = 1
    else:
        raise ValueError("Valid options are 'on' or 'off'")

    endpoint = "/router/api/v1/device/control"
    data = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": d_sku,
            "device": d_mac_addr,
            "capability": {
                "type": "devices.capabilities.on_off",
                "instance": "powerSwitch",
                "value": toggle_value
            }
        }
    }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Govee API error: {result.get('msg')}")
    print(f"Power turned {toggle}")


def change_govee_device_brightness(d_sku, d_mac_addr, value):

#   Sets brightness for a device.
#   value: integer between 1 and 100 (percent)

    if not isinstance(value, int):
        raise ValueError("Value must be an integer (e.g. 75)")

    endpoint = "/router/api/v1/device/control"
    data = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": d_sku,
            "device": d_mac_addr,
            "capability": {
                "type": "devices.capabilities.range",
                "instance": "brightness",
                "value": value
            }
        }
    }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Govee API error: {result.get('msg')}")
    print(f"Brightness set to {value}%")


def change_govee_device_scene(d_sku, d_mac_addr, param_id, scene_id):

#   Activates a scene on a device.
#   param_id and scene_id come from get_govee_device_scenes() or get_govee_device_diy_scenes().

    endpoint = "/router/api/v1/device/control"
    data = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": d_sku,
            "device": d_mac_addr,
            "capability": {
                "type": "devices.capabilities.dynamic_scene",
                "instance": "lightScene",
                "value": {
                    "paramId": param_id,
                    "id": scene_id
                }
            }
        }
    }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Govee API error: {result.get('msg')}")
    print(f"Scene (paramId={param_id}, id={scene_id}) applied")
