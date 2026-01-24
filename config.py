import json
import os
from pathlib import Path

APP_NAME = "fstasearch"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "include_directories": [str(Path.home())],
    "exclude_directories": [],
    "last_search": "",
    "path_display_depth": 3,
    "window_size": [1000, 400],
    "display_tooltips": True
}

def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            
        # Migration: handle old "target_directory"
        if "target_directory" in data:
            if "include_directories" not in data:
                data["include_directories"] = [data["target_directory"]]
            del data["target_directory"]
            
        # Merge with defaults to ensure all keys exist
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
