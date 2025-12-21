import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QFrame, QLabel, QButtonGroup)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from src.ui.pages.dashboard import DashboardPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYSTEMIZER")
        self.setFixedSize(900, 620) # Significantly increased size to prevent overlap
        
        # Set Icon
        from main import resource_path
        self.setWindowIcon(QIcon(resource_path("assets/icon.png")))
        
        # Dashboard Page as central widget
        self.dashboard_page = DashboardPage()
        self.setCentralWidget(self.dashboard_page)
