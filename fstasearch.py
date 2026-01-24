import sys
import argparse
import config
import logging
from indexer import Indexer
from gui import SearchWindow
from PyQt6.QtWidgets import QApplication

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    parser = argparse.ArgumentParser(description="A minimal file cataloger and launcher.")
    parser.add_argument("--configure", action="store_true", help="Set the target directory")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    
    # Load Config
    user_config = config.load_config()
    
    # Initialize Indexer
    include_dirs = user_config.get("include_directories", [])
    exclude_dirs = user_config.get("exclude_directories", [])
    
    # Validation: If no directories, default to home
    if not include_dirs:
        logging.warning("No include directories found. Defaulting to home.")
        # But we don't save this change implicitly? Or maybe we should?
        # For now let's just use home but prompt user in GUI to change it
        from pathlib import Path
        include_dirs = [str(Path.home())]

    indexer = Indexer(include_dirs, exclude_dirs)
    indexer.scan()

    # Show Window
    window = SearchWindow(indexer)
    window.show_window()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
