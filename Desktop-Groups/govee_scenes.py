import json
from govee_lights import get_govee_device_scenes, get_govee_lights


def get_govee_scenes():
    
    # Fetches all devices and their scenes, then saves to govee_scenes.json.
    # This is a helper script to populate govee_scenes.json, which is used by game_profiles.json.
    devices = get_govee_lights()
    all_scenes = {}

    for device in devices:
        name = device["d_name"]
        print(f"Fetching scenes for {name}...")

        response = get_govee_device_scenes(device["d_sku"], device["d_mac_addr"])
        capabilities = response.get("payload", {}).get("capabilities", [])

        scenes = []
        for cap in capabilities:
            options = cap.get("parameters", {}).get("options", [])
            for option in options:
                scenes.append({
                    "name": option["name"],
                    "id": option["value"]["id"],
                    "paramId": option["value"]["paramId"]
                })

        all_scenes[name] = {
            "sku": device["d_sku"],
            "mac": device["d_mac_addr"],
            "scenes": scenes
        }

    with open("govee_scenes.json", "w") as f:
        json.dump(all_scenes, f, indent=2)

    print(f"Done")

get_govee_scenes()