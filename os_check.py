import os
import platform
from ctypes import CDLL

def load_fluidsynth_dll():
    if platform.system() == "Windows":
        dll_path = r'C:\tools\fluidsynth\bin\libfluidsynth-3.dll'
        if os.path.exists(dll_path):
            CDLL(dll_path)
            print(f"Loaded DLL: {dll_path}")
        else:
            print(f"DLL not found: {dll_path}")

load_fluidsynth_dll()