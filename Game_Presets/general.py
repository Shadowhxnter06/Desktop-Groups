import json
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from govee_scenes import search_govee_scenes

def create_profile():
    # This function is meant to be called from the command line to create a new profile.
    # It will prompt the user for each setting and then save the profile to the JSON file.
    print("Creating a new profile...")
    profile_name = input("Enter a name for the profile: ")
    wallpaper = input("Enter the wallpaper profile name (or leave blank to skip): ")
    audio = input("Enter the audio output device name ('Speakers' or 'Headphones'): ")
    if audio.lower() == "speakers":
        audio = "Speakers (Realtek USB2.0 Audio)"
    elif audio.lower() == "headphones":
        audio = "Headset Earphone (G535 Wireless Gaming Headset)"
    else:
        print("Invalid audio device, defaulting to headset")
        audio = "Headset Earphone (G535 Wireless Gaming Headset)"
    govee_dreamview = input("Enable Dreamview for Govee devices? (y/n): ").lower()
    govee_settings = {}
    device_options = ["TV Backlight", "Light bar", "Covered LED Strip", "Table Lamp", "AI Gaming Sync Box Kit", "Glide Hexa Ultra", "Glide Hexa"]
    while govee_dreamview != "y":
        
        device_name = input(f"Enter a Govee device name to configure, valid options:\n {', '.join(device_options)}\n'done' to finish, 'skip' to skip: ")
        if device_name.lower() == "done":
            break
        if device_name.lower() == "skip":
            continue
        if device_name not in device_options:
            print(f"Invalid device name. Valid options are: {', '.join(device_options)}")
            continue
        
        power_state = input(f"Enter power state for {device_name} ('on' or 'off'): ")
        if power_state.lower() == "off":
            continue
        brightness = int(input(f"Enter brightness for {device_name} (1-100): "))
        scene_name = input(f"Enter the scene name for {device_name} (or leave blank to skip): ")
        if scene_name:
            scene_info = search_govee_scenes(device_name, scene_name)
            if scene_info:
                if "paramId" not in scene_info:
                    govee_settings[device_name] = {
                        "power": power_state,
                        "brightness": brightness,
                        "scene": {
                            "scene_id": scene_info["id"]
                        }
                    }
                elif "paramId" in scene_info:
                    govee_settings[device_name] = {
                        "power": power_state,
                        "brightness": brightness,
                        "scene": {
                            "scene_id": scene_info["id"],
                            "param_id": scene_info.get("paramId")
                        }
                    }
            else:
                print(f"Scene '{scene_name}' not found for device '{device_name}', skipping scene setting.")
                govee_settings[device_name] = {
                    "power": power_state,
                    "brightness": brightness
                }
        
        device_options.remove(device_name)
        if not device_options:
            print("All devices configured.")
            break
    
    if govee_dreamview == "y":
        govee_block = {"dreamview": True}
    else:
        govee_block = govee_settings

    profile = {
        profile_name: {
            "wallpaper": wallpaper,
            "audio": audio,
            "apps": [],
            "websites": [],
            "govee": govee_block
        }
    }
    confirmation = input(f"Profile configuration:\n{json.dumps(profile, indent=2)}\nDoes this look correct? ('y/n')")
    if confirmation.lower() != "y":
        print("Profile creation cancelled.")
        return
    else:
        with open("profiles.json", "r") as f:
            existing_profiles = json.load(f)
        if profile_name in existing_profiles:
            overwrite = input(f"A profile named '{profile_name}' already exists. Do you want to overwrite it? ('y/n'): ")
            if overwrite.lower() != "y":
                print("Profile creation cancelled.")
                return
            else:
                print(f"Overwriting existing profile '{profile_name}'")

        existing_profiles.update(profile)
        
        with open("profiles.json", "w") as f:
            json.dump(existing_profiles, f, indent=2)
            print(f"Profile '{profile_name}' added to 'profiles.json'")

create_profile()