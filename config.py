from pathlib import Path
import database

DEFAULT_CONFIG = {
    "include_directories": [str(Path.home())],
    "exclude_directories": [],
    "last_search": "",
    "path_display_depth": 3,
    "window_size": [1000, 400],
    "display_tooltips": True,
    "last_scan": 0 
}

def load_config():
    # Load each key from DB, falling back to DEFAULT_CONFIG
    config = {}
    for key, default_val in DEFAULT_CONFIG.items():
        config[key] = database.db.get_setting(key, default_val)
    return config

def save_config(config):
    for key, value in config.items():
        database.db.set_setting(key, value)

