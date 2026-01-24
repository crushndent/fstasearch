import sys
import os
import argparse
import config
import logging
from indexer import Indexer
from gui import SearchWindow
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtNetwork import QLocalSocket, QLocalServer
from PyQt6.QtCore import QIODevice

SOCKET_NAME = "fstasearch_socket"

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Try to connect to existing instance
    socket = QLocalSocket()
    socket.connectToServer(SOCKET_NAME)
    if socket.waitForConnected(500):
        logging.info("Instance already running. Sending show command...")
        socket.write(b"SHOW")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        sys.exit(0)

    # 2. If not running, start new instance
    logging.info("Starting new instance...")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep running when window is closed

    # Create Local Server
    server = QLocalServer()
    # Cleanup old socket if it exists (e.g. from crash)
    QLocalServer.removeServer(SOCKET_NAME)
    if not server.listen(SOCKET_NAME):
        logging.error(f"Unable to start local server: {server.errorString()}")
        # Proceed anyway? Or fail? Let's proceed but warn.
        
    parser = argparse.ArgumentParser(description="A minimal file cataloger and launcher.")
    parser.add_argument("--configure", action="store_true", help="Set the target directory")
    args = parser.parse_args()

    # Load Config
    user_config = config.load_config()
    
    # Initialize Indexer
    include_dirs = user_config.get("include_directories", [])
    exclude_dirs = user_config.get("exclude_directories", [])
    
    if not include_dirs:
        logging.warning("No include directories found. Defaulting to home.")
        from pathlib import Path
        include_dirs = [str(Path.home())]

    indexer = Indexer(include_dirs, exclude_dirs)
    indexer.scan()

    # Show Window
    window = SearchWindow(indexer)
    window.show_window()

    # Handle incoming connections (commands from other instances)
    def handle_new_connection():
        client_socket = server.nextPendingConnection()
        if client_socket.waitForReadyRead(1000):
            command = client_socket.readAll().data().decode().strip()
            if command == "SHOW":
                window.show_window()
        client_socket.disconnectFromServer()

    server.newConnection.connect(handle_new_connection)

    # System Tray
    tray_icon = QSystemTrayIcon(window)

    # Use custom icon
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icon.png")
    
    if os.path.exists(icon_path):
        from PyQt6.QtGui import QIcon
        tray_icon.setIcon(QIcon(icon_path))
    else:
        # Fallback
        from PyQt6.QtWidgets import QStyle
        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        tray_icon.setIcon(icon)

    tray_icon.setToolTip("fstasearch")
    
    tray_menu = QMenu()
    show_action = tray_menu.addAction("Show Search")
    show_action.triggered.connect(window.show_window)
    quit_action = tray_menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    # Connect trait activation (click) to show window
    tray_icon.activated.connect(lambda reason: window.show_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
