# This script will be used to open apps and change items when ran.
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add parent directory to path for imports


group = input("Homelab, Dev, or Gaming?: ") #Temporary. Will change this to either separate scripts or "buttons" of some sort

def group_functions(group):

    if group == "Gaming":

        game = input("What game would you like to play?: ")

        match(game):
            case "Elden Ring":
              #input executable path

        def gaming_group(game):
          
          app_list = ["Steam", "Discord", "Youtube"]
          change_list = ["Wallpaper", "Audio-Device"]