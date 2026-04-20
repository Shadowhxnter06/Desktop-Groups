import json
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from govee_lights import search_govee_scenes

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
    device_options = ["tv_backlight", "light_bar", "covered_led_strip", "table_lamp", "sync_box", "glide_hexa_ultra", "glide_hexa"]
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

def edit_profile(name):

    # Function to edit aspects of a specific profile from its name (case-sensitive)
    with open("profiles.json", "r") as f:
            existing_profiles = json.load(f)
    
    if name not in existing_profiles:
        print(f"Profile '{name}' not found. Input must be case-sensitive")
        return
    
    selected_profile = existing_profiles[name]
    
    while True:

        print(f"Current configuration: {json.dumps(selected_profile, indent=2)}")
        selected_option = (input(f"Which setting would you like to change? (Must be case-sensitive, 'done' to finish): "))
        
        if selected_option.lower() == "done":
            break

        match selected_option.lower():
            case "wallpaper":
                w_change = input(f"Enter name of new wallpaper profile: ")
                with open("profiles.json", "w") as f:
                    selected_profile["wallpaper"] = w_change
                    json.dump(existing_profiles, f, indent=2)
                    print(f"Wallpaper updated for profile '{name}'")
            case "audio":
                a_change = input(f"Enter name of new audio output device ('Speakers' or 'Headphones'): ")
                if a_change.lower() == "speakers":
                    a_change = "Speakers (Realtek USB2.0 Audio)"
                elif a_change.lower() == "headphones":
                    a_change = "Headset Earphone (G535 Wireless Gaming Headset)"
                else:
                    print("Invalid audio device, defaulting to headset")
                    a_change = "Headset Earphone (G535 Wireless Gaming Headset)"
                with open("profiles.json", "w") as f:
                    selected_profile["audio"] = a_change
                    json.dump(existing_profiles, f, indent=2)
                    print(f"Audio output updated for profile '{name}'")
            case "apps":
                app_change = input(f"Enter new list of apps to launch (comma-separated, no spaces): ")
                app_list = app_change.split(",")
                with open("profiles.json", "w") as f:
                    selected_profile["apps"] = app_list
                    json.dump(existing_profiles, f, indent=2)
                    print(f"Apps updated for profile '{name}'")
            case "websites":
                web_change = input(f"Enter new list of websites to open (comma-separated, no spaces): ")
                web_list = web_change.split(",")
                with open("profiles.json", "w") as f:
                    selected_profile["websites"] = web_list
                    json.dump(existing_profiles, f, indent=2)
                    print(f"Websites updated for profile '{name}'")
            case "govee":
                govee_device = input(f"Which Govee device would you like to update? (e.g. 'table_lamp', 'glide_hexa', case-sensitive): ")
                if govee_device not in selected_profile["govee"]:
                    print(f"Device '{govee_device}' not found in profile '{name}'")
                    continue
                setting_to_change = input(f"What setting would you like to change for '{govee_device}'? ('power', 'brightness', 'scene'): ")
                match setting_to_change.lower():
                    case "power":
                        new_power = input(f"Enter new power state ('on' or 'off'): ")
                        if new_power.lower() not in ["on", "off"]:
                            print("Invalid power state. Must be 'on' or 'off'.")
                            continue
                        selected_profile["govee"][govee_device]["power"] = new_power
                    case "brightness":
                        new_brightness = int(input(f"Enter new brightness (1-100): "))
                        if not (1 <= new_brightness <= 100):
                            print("Invalid brightness. Must be between 1 and 100.")
                            continue
                        selected_profile["govee"][govee_device]["brightness"] = new_brightness
                    case "scene":
                        new_scene_name = input(f"Enter the name of the new scene: ")
                        scene_info = search_govee_scenes(govee_device, new_scene_name)
                        if scene_info:
                            if "paramId" not in scene_info:
                                selected_profile["govee"][govee_device]["scene"] = {
                                    "scene_id": scene_info["id"]
                                }
                            elif "paramId" in scene_info:
                                selected_profile["govee"][govee_device]["scene"] = {
                                    "scene_id": scene_info["id"],
                                    "param_id": scene_info.get("paramId")
                                }
                        else:
                            print(f"Scene '{new_scene_name}' not found for device '{govee_device}', skipping scene update.")
                            continue
                with open("profiles.json", "w") as f:
                    json.dump(existing_profiles, f, indent=2)
                    print(f"Govee settings updated for profile '{name}'")
            case _:
                print("Invalid option selected.")
                continue
            # Eventually need to add other options such as Divoom, overheads, other wallpaper configs etc

edit_profile("Temp")