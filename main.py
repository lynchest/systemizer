import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils import resource_path

def load_stylesheet(app):
    path = resource_path("src/ui/styles/theme.qss")
    with open(path, "r") as f:
        app.setStyleSheet(f.read())

def main():
    app = QApplication(sys.argv)
    
    # Load Theme
    try:
        load_stylesheet(app)
    except FileNotFoundError:
        print("Warning: theme.qss not found!")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
