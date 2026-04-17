import os
import wmi
import json
import comtypes
from pycaw.pycaw import AudioUtilities
from pycaw.constants import EDataFlow
import subprocess
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add parent directory to path for imports
from govee_lights import (
    toggle_govee_device_power,
    change_govee_device_brightness,
    change_govee_device_scene,
    build_govee_device_map,
    toggle_govee_dreamview
)

# ---------------------------------------------------------------------------
# FUNCTION DEFINING
# ---------------------------------------------------------------------------

# Function to change desktop audio output device
def audio_output_change(a_device):

    speakers = "Speakers (Realtek USB2.0 Audio)"
    headset = "Headset Earphone (G535 Wireless Gaming Headset)"

    valid = [speakers, headset]
    if a_device not in valid:
        raise ValueError

    # Code to toggle audio output device (between speakers and headset)
    comtypes.CoInitialize()
    audio_devices = AudioUtilities.GetAllDevices(data_flow=EDataFlow.eRender.value)
    for d in audio_devices:
        if d.FriendlyName == a_device:
            AudioUtilities.SetDefaultDevice(d.id)
            return None
    return "Device Not Found"

# Function to change the Wallpaper Engine wallpaper(s) to a pre-defined profile
def wallpaper_change(we_profile):

    we_exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine\wallpaper64.exe"
    #we_wallpapers_path = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\431960"

    result = subprocess.run([
        we_exe_path,
        "-control", "openProfile",
        "-profile", we_profile])
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        #print("Wallpaper changed successfully.")
        pass

# Creates the govee device map at startup
govee_device_map = build_govee_device_map()

# Looks up a govee device's SKU and MAC address by its nickname.
def get_govee_device_info(nickname):

#    Uses the govee_device_map built at startup from the live API.
#    Example: get_govee_device_info("table_lamp") -> ("H6022", "AB:CD:...")
    if nickname not in govee_device_map:
        raise ValueError(f"'{nickname}' not found in govee-devices.json or your Govee account.")

    device = govee_device_map[nickname]
    return device["sku"], device["mac"]

# ---------------------------------------------------------------------------
# LOAD CONFIG FILES
# os.path.dirname(__file__) gives us the folder this script lives in,
# so the JSON paths work no matter where you run the script from.
# ---------------------------------------------------------------------------

game_list_path    = os.path.join(os.path.dirname(__file__), "game_list.json")
profiles_path = os.path.join(os.path.dirname(__file__), "profiles.json")

with open(game_list_path, "r") as f:
    game_list = json.load(f)

with open(profiles_path, "r") as f:
    game_presets = json.load(f)

# ---------------------------------------------------------------------------
# PROFILE LOADING
# This function reads a game's entry from game-presets.json and applies
# every setting it finds: wallpaper, audio, and per-device Govee changes.
# ---------------------------------------------------------------------------

def apply_profile(game_name):

#    Looks up game_name in game_presets.json and applies its full profile.
    if game_name not in game_presets:
        print(f"No profile found for '{game_name}'. Applying default.") # -------------------------------------- May need to change this if it starts applying profiles when other applications are launched
        game_name = "default"

    if game_name not in game_presets:
        print("No default profile configured either. Skipping.")
        return

    profile = game_presets[game_name]

    # --- Wallpaper ---
    if "wallpaper" in profile:
        #print(f"Setting wallpaper profile: {profile['wallpaper']}")
        wallpaper_change(profile["wallpaper"])

    # --- Audio Device ---
    if "audio" in profile:
        #print(f"Setting audio device: {profile['audio']}")
        audio_output_change(profile["audio"])

    # --- Govee Lights ---
    # Loop over each device and apply whatever settings are listed for it.
    if "govee" in profile:
        
        dreamview = profile["govee"].get("dreamview", False)

        if dreamview:
            #print("Dreamview enabled, applying device states")

            dreamview_off = ("tv_backlight", "light_bar", "covered_led_strip", "table_lamp")
            dreamview_on = ("sync_box", "glide_hexa_ultra", "glide_hexa")

            for nickname in dreamview_on:
                try:
                    sku, mac = get_govee_device_info(nickname)
                    toggle_govee_device_power(sku, mac, "on")
                    if nickname == "sync_box":
                        toggle_govee_dreamview(sku, mac, "on")
                except ValueError as e:
                    print(f"Skipping '{nickname}': {e}")
            
            for nickname in dreamview_off:
                try:
                    sku, mac = get_govee_device_info(nickname)
                    toggle_govee_device_power(sku, mac, "off")
                except ValueError as e:
                    print(f"Skipping '{nickname}': {e}")

        else:
            
            for nickname, settings in profile["govee"].items():
                try:
                    sku, mac = get_govee_device_info(nickname)
                except ValueError as e:
                    print(f"Skipping '{nickname}': {e}")
                    continue

                if "power" in settings:
                    toggle_govee_device_power(sku, mac, settings["power"])

                if "brightness" in settings:
                    change_govee_device_brightness(sku, mac, settings["brightness"])

                if "scene" in settings:
                    scene = settings["scene"]
                    if "scene_id" in scene and "param_id" in scene:
                        change_govee_device_scene(sku, mac, scene["scene_id"], scene["param_id"])
                    elif "scene_id" in scene:
                        change_govee_device_scene(sku, mac, scene["scene_id"])
                    else:
                        print(f"Invalid scene settings for '{nickname}', skipping scene change.")
                        continue

# ---------------------------------------------------------------------------
# PROCESS WATCHER
# Watches for new processes starting on Windows. When one matches a game
# in game-list.json, it triggers the profile runner.
# ---------------------------------------------------------------------------

# Establishing "connection" with Windows system via wmi
c = wmi.WMI()

# Sets up a listening process stored in the object "watcher"
watcher = c.Win32_Process.watch_for(
    notification_type = "creation", # Only listen for new processes
    delay_secs= 1 # Windows checks every 1 second for new matching events
)

print("Waiting for games to launch...")

# Infinite loop, keeps the script checking for events.
while True:
    event = watcher() # Pauses execution and waits until Windows runs a process, which is then stored as "event"
    
    exe_filename = os.path.basename(event.ExecutablePath or "")

    if exe_filename in game_list: # Checks if the executable is in the JSON file, if not it the loop goes back to "watcher()"
        game_name = game_list[exe_filename]["name"] # Grabs game name from dictionary

        #print(f"Detected: {game_name}")
        apply_profile(game_name)
        process_id = event.ProcessId

        # Creates a new watcher to check for the game closing and revert to previous configurations
        c_watcher = c.Win32_Process.watch_for(
            notification_type = "deletion",
            delay_secs= 1,
            ProcessId = process_id
        )