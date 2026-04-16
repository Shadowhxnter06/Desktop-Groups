import subprocess

we_profile = input("Profile Name: ")

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

wallpaper_change(we_profile)