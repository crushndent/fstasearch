# fstasearch

A minimal, fast file cataloger and launcher for Linux. `fstasearch` allows you to quickly find and access files and directories from your search path.

## Features

- **Blazing Fast**: Scans and indexes directories for quick retrieval.
- **Minimal Interface**: A clean, unobtrusive search window.
- **Smart Path Truncation**: Displays paths clearly by truncating leading directories.
- **Configurable**: Customize included folders, exclusion patterns, and appearance.
- **Clipboard Integration**: Click or press Enter to copy the path to the clipboard.
- **Explorer Integration**: Right-click to open the file location in your file explorer.

## Installation

1. Clone the repository.
2. Ensure you have Python 3 and PyQt6 installed.
   ```bash
   pip install PyQt6
   ```

## Usage

Run the application:
```bash
python fstasearch.py
```

### Shortcuts

- **Enter** or **Left Click**: Copy the selected path to the clipboard/
- **Right Click**: Open the context menu to visit the file in your file manager.
- **Esc**: Close the window (saves state).

### Configuration

Click the **Gear Icon (⚙)** in the search bar to open settings.

- **Include Folders**: Add directories to scan.
- **Exclude Folders**: Add directories to ignore.
- **Appearance**:
    - **Path Display Depth**: Control how many folder levels are shown in the result list.
    - **Show Tooltips**: Toggle the "Left click to copy, Right click to visit" tooltip hints.
