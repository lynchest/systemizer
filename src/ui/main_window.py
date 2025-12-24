import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QFrame, QLabel, QButtonGroup)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from src.ui.pages.dashboard import DashboardPage
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.settings import get_settings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYSTEMIZER")
        self.resize(900, 650) # Initial size, but resizable
        self.setMinimumWidth(600) # Keep width fixed-ish or minimum
        
        # Initialize settings
        self.settings = get_settings()
        
        # Set Icon
        from main import resource_path
        self.setWindowIcon(QIcon(resource_path("assets/icon.png")))
        
        # Dashboard Page as central widget
        self.dashboard_page = DashboardPage()
        
        # Create central widget with settings button
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        
        # Top bar with settings button
        top_bar = self.create_top_bar()
        central_layout.addWidget(top_bar)
        
        # Dashboard content
        central_layout.addWidget(self.dashboard_page)
        
        self.setCentralWidget(central_widget)
        
        # Apply theme on startup
        self.apply_theme()
    
    def create_top_bar(self):
        """Create top bar with settings button."""
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 46, 80);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(8)

        # Title centered in top bar
        try:
            gpu_name = self.dashboard_page.gpu_monitor.gpu_name if hasattr(self.dashboard_page, 'gpu_monitor') and hasattr(self.dashboard_page.gpu_monitor, 'gpu_name') else "System"
        except Exception:
            gpu_name = "System"
        title = QLabel(f"SYSTEMIZER — {gpu_name}")
        title.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)

        # Left spacer, title, then settings button on right
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        
        # Settings button (use icon instead of emoji)
        from main import resource_path
        settings_btn = QPushButton()
        settings_btn.setFixedSize(36, 36)
        settings_btn.setIcon(QIcon(resource_path("assets/gear.svg")))
        settings_btn.setIconSize(QSize(18, 18))
        settings_btn.setToolTip("Settings")
        settings_btn.setAccessibleName("Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.10);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,0.28);
                border-radius: 8px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.18);
                border: 1px solid rgba(255,255,255,0.36);
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.25);
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        return top_bar
    
    def open_settings(self):
        """Open the settings dialog."""
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.on_settings_changed)
        settings_dialog.theme_changed.connect(self.apply_theme)

        # Ensure dialog is application-modal and stays above the main window
        settings_dialog.setWindowModality(Qt.ApplicationModal)
        settings_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        # Center the dialog over the main window
        settings_dialog.adjustSize()
        parent_geo = self.geometry()
        dx = (parent_geo.width() - settings_dialog.width()) // 2
        dy = (parent_geo.height() - settings_dialog.height()) // 2
        settings_dialog.move(parent_geo.x() + dx, parent_geo.y() + dy)

        # Exec will block and show it on top
        settings_dialog.exec()

        # Clear the always-on-top flag after closing
        settings_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, False)
    
    def on_settings_changed(self):
        """Handle settings changes."""
        # Signal the dashboard to refresh
        if hasattr(self.dashboard_page, 'refresh_visibility'):
            self.dashboard_page.refresh_visibility()
    def apply_theme(self):
        """Apply background color from settings to the application."""
        # Get background color from settings
        bg_color = self.settings.get_theme_color("background_main")
        
        # Calculate lighter shade for secondary elements
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        bg_alt = '#{:02x}{:02x}{:02x}'.format(
            min(int(bg_rgb[0] * 1.15), 255),
            min(int(bg_rgb[1] * 1.15), 255),
            min(int(bg_rgb[2] * 1.15), 255)
        )
        
        # Create dynamic stylesheet with only the background color
        main_stylesheet = f"""
            QMainWindow {{
                background-color: {bg_color};
            }}
            
            QWidget {{
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 14px;
                color: #cdd6f4;
            }}
            
            QFrame#Sidebar {{
                background-color: {bg_alt};
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QPushButton#NavButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                text-align: left;
                color: #a6adc8;
                font-weight: bold;
            }}
            
            QPushButton#NavButton:hover {{
                background-color: {bg_alt};
                color: #cdd6f4;
            }}
            
            QPushButton#NavButton:checked {{
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border-left: 3px solid #a6e3a1;
            }}
            
            QFrame.Card {{
                background-color: {bg_alt};
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QLabel#CardTitle {{
                color: #a6adc8;
                font-size: 10px;
                font-weight: bold;
            }}
            
            QLabel#CardValue {{
                color: #cdd6f4;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QProgressBar {{
                border: none;
                background-color: {bg_alt};
                border-radius: 4px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: #a6e3a1;
                border-radius: 4px;
            }}
        """
        
        # Apply the stylesheet to main window
        self.setStyleSheet(main_stylesheet)