import os
import wmi
import json
import comtypes
from pycaw.pycaw import AudioUtilities
from pycaw.constants import EDataFlow
import subprocess
import sys
from govee_lights import (
    get_govee_lights,
    toggle_govee_device_power,
    change_govee_device_brightness,
    change_govee_device_scene
)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add parent directory to path for imports

# ---------------------------------------------------------------------------
# FUNCTION DEFINING
# ---------------------------------------------------------------------------

# Function to change desktop audio output device
def audio_output_change(a_device):

    speakers = "Speakers (Realtek USB2.0 Audio)"
    headset = "Headset Earphone (G535 Wireless Gaming Headset"

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
        print("Wallpaper changed successfully.")

# Calls the Govee API to get all current devices, then matches them against the nicknames in govee_devices.json.
def build_govee_device_map():
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
game_presets_path = os.path.join(os.path.dirname(__file__), "game_profiles.json")

with open(game_list_path, "r") as f:
    game_list = json.load(f)

with open(game_presets_path, "r") as f:
    game_presets = json.load(f)

# ---------------------------------------------------------------------------
# PROFILE LOADING
# This function reads a game's entry from game-presets.json and applies
# every setting it finds: wallpaper, audio, and per-device Govee changes.
# ---------------------------------------------------------------------------

def apply_profile(game_name):

#    Looks up game_name in game_presets.json and applies its full profile.
#    If the game has no entry, a default profile is applied instead.
#    Fall back to a "default" profile if this game isn't configured yet.

    if game_name not in game_presets:
        print(f"No profile found for '{game_name}'. Applying default.") # -------------------------------------- May need to change this if it starts applying profiles when other applications are launched
        game_name = "default"

    if game_name not in game_presets:
        print("No default profile configured either. Skipping.")
        return

    profile = game_presets[game_name]

    # --- Wallpaper ---
    if "wallpaper" in profile:
        print(f"Setting wallpaper profile: {profile['wallpaper']}")
        wallpaper_change(profile["wallpaper"])

    # --- Audio Device ---
    if "audio" in profile:
        print(f"Setting audio device: {profile['audio']}")
        audio_output_change(profile["audio"])

    # --- Govee Lights ---
    # profile["govee"] is a dict like:
    #   { "table_lamp": {"power": "on", "brightness": 60, "scene": {...}}, ... }
    # Loop over each device and apply whatever settings are listed for it.
    if "govee" in profile:
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

            # "scene" is optional — some devices in a profile might just be turned on/off
            if "scene" in settings:
                scene = settings["scene"]
                change_govee_device_scene(sku, mac, scene["param_id"], scene["scene_id"])
    
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
        print(f"Detected: {game_name}")
        apply_profile(game_name)