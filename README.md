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

> **Setup Tip**: Bind this command to a **Keyboard Shortcut** in your specific Desktop Environment (e.g., `Super+Space` or `Alt+F2`).
> Since `fstasearch` runs as a single-instance background service, hitting this shortcut will instantly summon the window.

### Background Service / Single Instance
`fstasearch` runs as a background service. 
- **First Launch**: Starts the service, scans files, and shows the window.
- **Subsequent Launches**: Instantly opens the existing search window (no startup delay).
- **Closing the Window**: Hides the window but keeps the application running in the background.
- **System Tray**: A tray icon is available to manually "Show Search" or "Quit" the application entirely.

### Shortcuts

- **Type**: Start typing to filter results.
- **Up/Down**: Navigate through the result list.
- **Enter** or **Left Click**: Copy the selected path to the clipboard and **hide window**.
- **Right Click**: Open the context menu to visit the file in your file manager.
- **Esc**: Hide the window.

### Configuration

Click the **Gear Icon (⚙)** in the search bar to open settings.

- **Include Folders**: Add directories to scan.
- **Exclude Folders**: Add directories to ignore.
- **Appearance**:
    - **Path Display Depth**: Control how many folder levels are shown in the result list.
    - **Show Tooltips**: Toggle the "Left click to copy, Right click to visit" tooltip hints.
