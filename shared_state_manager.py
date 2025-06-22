# shared_state_manager.py
import os
import time

FLAG_FILE = "shared_flag.txt"

def write_flag(value: bool):
    """Writes the boolean value to the shared flag file."""
    try:
        with open(FLAG_FILE, "w") as f:
            f.write(str(value))
        print(f"[{os.getpid()}] Flag written: {value}")
    except IOError as e:
        print(f"[{os.getpid()}] Error writing flag file: {e}")

def read_flag() -> bool:
    """Reads the boolean value from the shared flag file."""
    try:
        if not os.path.exists(FLAG_FILE):
            # If the file doesn't exist, assume a default (e.g., False)
            # Or you might want to initialize it to False here
            write_flag(False) # Initialize if not present
            return False
        with open(FLAG_FILE, "r") as f:
            content = f.read().strip()
            return content.lower() == "true"
    except IOError as e:
        print(f"[{os.getpid()}] Error reading flag file: {e}")
        return False # Default to False on error
    except Exception as e:
        print(f"[{os.getpid()}] Unexpected error reading flag file: {e}")
        return False # Default to False on unexpected error

def initialize_flag(initial_value: bool = False):
    """Initializes the flag file with a given value if it doesn't exist."""
    if not os.path.exists(FLAG_FILE):
        write_flag(initial_value)
        print(f"[{os.getpid()}] Initialized flag file with: {initial_value}")