import os
import platform
from ctypes import CDLL

def load_fluidsynth_dll():
    if platform.system() == "Windows":
        # Add the Fluidsynth bin directory
        dll_dir_fluidsynth = r"C:\tools\fluidsynth\bin"

        # Add the SDL bin directory (if that's where SDL3.dll is)
        dll_dir_sdl = r"C:\libs\SDL3-3.2.8\x86_64-w64-mingw32\bin"

        os.add_dll_directory(dll_dir_fluidsynth)
        os.add_dll_directory(dll_dir_sdl)

        # Build the path to the Fluidsynth DLL
        dll_path = os.path.join(dll_dir_fluidsynth, "libfluidsynth-3.dll")

        if os.path.exists(dll_path):
            # Now that we've added the DLL directories, load the DLL
            CDLL(dll_path)
            print(f"Loaded Fluidsynth DLL: {dll_path}")
        else:
            print(f"Fluidsynth DLL not found: {dll_path}")

# Call the function to load Fluidsynth
load_fluidsynth_dll()
