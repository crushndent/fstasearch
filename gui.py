import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLineEdit, QLabel, QListWidgetItem, QGraphicsDropShadowEffect,
                             QPushButton, QDialog, QTabWidget, QFileDialog, QToolButton,
                             QSpinBox, QFormLayout, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QGuiApplication, QClipboard, QIcon, QAction

import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.config = current_config or config.DEFAULT_CONFIG.copy()
        self.setWindowTitle("FstaSearch Settings")
        self.resize(500, 450)
        self.setup_ui()
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QListWidget { background-color: #3b3b3b; color: #e0e0e0; border: 1px solid #1a1a1a; }
            QPushButton { background-color: #4a90e2; color: white; border: none; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #357abd; }
            QTabWidget::pane { border: 1px solid #3d3d3d; }
            QTabBar::tab { background: #3b3b3b; color: #e0e0e0; padding: 8px; }
            QTabBar::tab:selected { background: #2b2b2b; border-bottom: 2px solid #4a90e2; }
            QSpinBox { background-color: #3b3b3b; color: #e0e0e0; border: 1px solid #1a1a1a; padding: 5px; }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Include Tab
        self.include_list = QListWidget()
        self.include_list.addItems(self.config.get("include_directories", []))
        self.tabs.addTab(self._create_list_tab(self.include_list, is_include=True), "Include Folders")
        
        # Exclude Tab
        self.exclude_list = QListWidget()
        self.exclude_list.addItems(self.config.get("exclude_directories", []))
        self.tabs.addTab(self._create_list_tab(self.exclude_list, is_include=False), "Exclude Folders")
        
        # Appearance Tab
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Rescan")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #555; color: white;")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_list_tab(self, list_widget, is_include):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Folder")
        add_btn.clicked.connect(lambda: self.add_folder(list_widget))
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(lambda: self.remove_selected(list_widget))
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        return widget

    def _create_appearance_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 20)
        self.depth_spin.setValue(self.config.get("path_display_depth", 3))
        self.depth_spin.setSuffix(" folders")
        layout.addRow("Path Display Depth:", self.depth_spin)

        return widget

    def add_folder(self, list_widget):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder", 
            "", 
            QFileDialog.Option.DontUseNativeDialog
        )
        if folder:
            list_widget.addItem(folder)

    def remove_selected(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def save(self):
        includes = [self.include_list.item(i).text() for i in range(self.include_list.count())]
        excludes = [self.exclude_list.item(i).text() for i in range(self.exclude_list.count())]
        
        self.config["include_directories"] = includes
        self.config["exclude_directories"] = excludes
        self.config["path_display_depth"] = self.depth_spin.value()
        
        config.save_config(self.config)
        self.accept()

class SearchWindow(QWidget):
    def __init__(self, indexer):
        super().__init__()
        self.indexer = indexer
        self.settings_dialog_open = False
        self.app_config = config.load_config() # Load config once into instance
        
        # Resizing state
        self._resizing = False
        self._resize_edge = None
        self._resize_margin = 10
        
        self.setup_ui()
        self.load_state()
        self.setMouseTracking(True) # Required for edge detection
        
    def setup_ui(self):
        # Window attributes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Layout & Container for styling
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Margin for shadow/resize handles
        
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.container)

        # Styling
        self.setStyleSheet("""
            QWidget#Container {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #3b3b3b;
                color: #e0e0e0;
                border: 1px solid #1a1a1a;
                border-radius: 4px;
                padding: 8px;
                padding-right: 30px; 
                font-size: 16px;
                selection-background-color: #4a90e2;
            }
            QListWidget {
                background-color: #2b2b2b;
                color: #cccccc;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                color: white;
                border-radius: 4px;
            }
            QToolButton#SettingsParams {
                background-color: transparent;
                border: none;
                color: #888;
                font-size: 12px;
            }
            QToolButton#SettingsParams:hover {
                color: #ddd;
            }
        """)

        # Search Bar Layout
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar_container = QWidget()
        self.search_bar_layout = QHBoxLayout(self.search_bar_container)
        self.search_bar_layout.setContentsMargins(0,0,0,0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        
        # Settings Button (inside search bar visual or next to it)
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.setObjectName("SettingsParams")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.search_bar_layout.addWidget(self.search_bar)
        self.search_bar_layout.addWidget(self.settings_btn)

        self.container_layout.addWidget(self.search_bar_container)

        # Results List
        self.results_list = QListWidget()
        self.results_list.itemActivated.connect(self.copy_to_clipboard)
        self.results_list.itemClicked.connect(self.copy_to_clipboard) # Left Click
        
        # Right Click Context Menu
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.open_context_menu)
        
        self.container_layout.addWidget(self.results_list)

        # Resizing
        size = self.app_config.get("window_size", [1000, 400])
        # Validate size type just in case config is old
        if not isinstance(size, list) or len(size) != 2:
            size = [1000, 400]
        self.resize(size[0], size[1])
        self.center_on_screen()

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.container.setGraphicsEffect(shadow)

    def load_state(self):
        last_search = self.app_config.get("last_search", "")
        if last_search:
            self.search_bar.setText(last_search)
            self.search_bar.selectAll()

    def save_state(self):
        self.app_config["last_search"] = self.search_bar.text()
        self.app_config["window_size"] = [self.width(), self.height()]
        config.save_config(self.app_config)

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def show_window(self):
        self.load_state()
        self.search_bar.setFocus()
        self.search_bar.selectAll()
        self.show()
        self.activateWindow()
    
    def _truncate_path(self, path):
        depth = self.app_config.get("path_display_depth", 3)
        parts = path.split(os.sep)
        if len(parts) > depth:
            return os.sep.join(["..."] + parts[-depth:])
        return path

    def on_search_text_changed(self, text):
        self.results_list.clear()
        if len(text.strip()) == 0:
            return
            
        matches = self.indexer.search(text)
        for match in matches:
            display_text = self._truncate_path(match)
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, match) # Store full path
            item.setToolTip(match)
            self.results_list.addItem(item)
        
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def open_settings(self):
        self.settings_dialog_open = True
        dlg = SettingsDialog(self, config.load_config())
        if dlg.exec():
            # Reload everything
            self.app_config = config.load_config()
            
            # Update indexer with new paths
            self.indexer.include_dirs = self.app_config.get("include_directories", [])
            self.indexer.exclude_dirs = self.app_config.get("exclude_directories", [])
            self.indexer.scan()
            
            # Refresh search to apply truncation
            self.on_search_text_changed(self.search_bar.text())
        
        self.settings_dialog_open = False
        self.search_bar.setFocus()

    def event(self, event):
        # Handle focus loss to close window
        if event.type() == QEvent.Type.WindowDeactivate:
            # If settings dialog is open, don't close main window
            if not self.settings_dialog_open:
                self.save_state()
                self.close()
        return super().event(event)
    
    def open_context_menu(self, pos):
        item = self.results_list.itemAt(pos)
        if not item:
            return
            
        full_path = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        open_action = QAction("Open in Explorer", self)
        open_action.triggered.connect(lambda: self._open_in_explorer(full_path))
        menu.addAction(open_action)
        
        menu.exec(self.results_list.mapToGlobal(pos))

    def _open_in_explorer(self, path):
        import subprocess
        
        if not os.path.exists(path):
            return
            
        target = path
        # If it's a file, we want to open the parent folder (and maybe select the file, but standard xdg-open opens parent)
        # Actually xdg-open on a file usually opens it in default app (editor/viewer).
        # User requested "Open Explorer IN the path".
        # If path is a file, opening explorer usually means opening the parent dir.
        if os.path.isfile(path):
            target = os.path.dirname(path)
            
        try:
            subprocess.Popen(['xdg-open', target])
            self.save_state()
            # self.close() # Keep window open, allow focus loss to close it
        except Exception as e:
            print(f"Error opening explorer: {e}")

    # --- Resizing Logic ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._detect_edge(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._drag_pos = event.globalPosition().toPoint()
            else:
                self._resizing = False
                
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._resize_edge = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            # Current mouse position in global coordinates
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._drag_pos
            geo = self.geometry()
            
            # Minimum size constraints
            min_w, min_h = 400, 100
            
            # Calculate new geometry based on edge
            if 'right' in self._resize_edge:
                new_w = max(min_w, geo.width() + delta.x())
                geo.setWidth(new_w)
                self._drag_pos.setX(current_pos.x()) # Only update if we actually moved
                
            if 'left' in self._resize_edge:
                new_w = max(min_w, geo.width() - delta.x())
                if new_w != geo.width():
                    geo.setLeft(geo.left() + delta.x())
                    self._drag_pos.setX(current_pos.x())

            if 'bottom' in self._resize_edge:
                new_h = max(min_h, geo.height() + delta.y())
                geo.setHeight(new_h)
                self._drag_pos.setY(current_pos.y())
                
            if 'top' in self._resize_edge:
                new_h = max(min_h, geo.height() - delta.y())
                if new_h != geo.height():
                    geo.setTop(geo.top() + delta.y())
                    self._drag_pos.setY(current_pos.y())
            
            self.setGeometry(geo)
        else:
            edge = self._detect_edge(event.pos())
            if not edge:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            elif edge in ['left', 'right']:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge in ['top', 'bottom']:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif edge in ['top_left', 'bottom_right']:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge in ['top_right', 'bottom_left']:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)

        super().mouseMoveEvent(event)

    def _detect_edge(self, pos):
        m = self._resize_margin
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        
        edge = ""
        
        # Check vertical
        if y < m:
            edge += "top"
        elif y > h - m:
            edge += "bottom"
            
        # Check horizontal
        if x < m:
            edge += "_" if edge else ""
            edge += "left"
        elif x > w - m:
            edge += "_" if edge else ""
            edge += "right"
            
        return edge if edge else None
        # Ensure the application process terminates
        QApplication.instance().quit()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.save_state()
            self.close()
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.results_list.setFocus()
            if self.results_list.count() > 0:
                if self.results_list.currentRow() == -1:
                    self.results_list.setCurrentRow(0)
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.results_list.hasFocus() or self.search_bar.hasFocus():
                self.copy_to_clipboard()
        else:
            super().keyPressEvent(event)
            if not self.search_bar.hasFocus() and event.text().isprintable():
                self.search_bar.setFocus()
                self.search_bar.setText(self.search_bar.text() + event.text())

    def copy_to_clipboard(self):
        self.save_state()
        current_item = self.results_list.currentItem()
        if current_item:
            full_path = current_item.data(Qt.ItemDataRole.UserRole)
            clipboard = QApplication.clipboard()
            clipboard.setText(full_path)
            print(f"Copied to clipboard: {full_path}")
            # self.close() # Keep window open as requested
        else:
            if self.results_list.count() > 0:
                item = self.results_list.item(0)
                full_path = item.data(Qt.ItemDataRole.UserRole)
                clipboard = QApplication.clipboard()
                clipboard.setText(full_path)
                print(f"Copied to clipboard: {full_path}")
                # self.close() # Keep window open as requested
