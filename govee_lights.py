import requests
import uuid
import os
import json
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

def build_govee_device_map():

# Calls the Govee API to get all current devices, then matches them against the nicknames in govee_devices.json.
#    Returns a dict like:
#    {
#        "glide_hexa_ultra": {"sku": "H606A", "mac": "AB:CD:..."},
#        "table_lamp":       {"sku": "H6022", "mac": "EF:GH:..."},
#        ...
#    }
    
    # Load nickname -> Govee app name mapping from JSON
    nicknames_json = os.path.join(os.path.dirname(__file__), "govee_devices.json")
    with open(nicknames_json, "r") as f:
        nicknames = json.load(f)  # e.g. {"glide_hexa_ultra": "Glide Hexa Ultra", ...}

    # Fetch device list from Govee API
    list_devices = get_govee_lights()  # Returns list of {d_name, d_sku, d_mac_addr}

    # Build a quick lookup: Govee app name -> {sku, mac}
    device_lookup = {device["d_name"]: {"sku": device["d_sku"], "mac": device["d_mac_addr"]} for device in list_devices}

    # Match nicknames to live devices
    device_map = {}
    for nickname, device_name in nicknames.items():
        if device_name in device_lookup:
            device_map[nickname] = device_lookup[device_name]
        else:
            print(f"Warning: '{device_name}' not found in your Govee account. Check govee_devices.json.")

    return device_map



# ---------------------------------------------------------------------------
# SCENE DISCOVERY
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
    #print(f"Power turned {toggle}")

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
    #print(f"Brightness set to {value}%")

def change_govee_device_scene(d_sku, d_mac_addr, scene_id, param_id=None):

#   Activates a scene on a device.
#   param_id and scene_id come from get_govee_device_scenes() or get_govee_device_diy_scenes().

    endpoint = "/router/api/v1/device/control"

    if param_id is None:
        # For DIY scenes
         data = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": d_sku,
                "device": d_mac_addr,
                "capability": {
                    "type": "devices.capabilities.diy_color_setting",
                    "instance": "diyScene",
                    "value": scene_id
                }
            }
        }
    else:
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
    #print(f"Scene applied")

# Looks up a govee device's SKU and MAC address by its nickname.
def get_govee_device_info(nickname):

    govee_device_map = build_govee_device_map()

#    Uses the govee_device_map built at startup from the live API.
#    Example: get_govee_device_info("table_lamp") -> ("H6022", "AB:CD:...")
    if nickname not in govee_device_map:
        raise ValueError(f"'{nickname}' not found in govee-devices.json or your Govee account.")

    device = govee_device_map[nickname]
    return device["sku"], device["mac"]

def toggle_govee_dreamview(d_sku, d_mac_addr, toggle):
    
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
                "type": "devices.capabilities.toggle",
                "instance": "dreamViewToggle",
                "value": toggle_value
                }
            }
        }
    response = requests.post(url=DOMAIN + endpoint, headers=HEADERS, json=data)
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Govee API error: {result.get('msg')}")
    #print(f"DreamView Toggled {toggle}")
