import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.exceptions import ThemeNotFoundError

# --- Basic Logging Setup ---
# This provides visibility into the application's startup and error states.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource. This works for both development
    and for a PyInstaller bundled application.
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # _MEIPASS is not set, so we're likely running in a normal Python environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_stylesheet(app: QApplication) -> None:
    """
    Loads the main stylesheet and applies it to the application.

    Args:
        app: The QApplication instance.

    Raises:
        ThemeNotFoundError: If the theme.qss file cannot be found at the expected path.
    """
    path = resource_path("src/ui/styles/theme.qss")
    if not os.path.exists(path):
        raise ThemeNotFoundError(f"Theme file not found at '{path}'")

    try:
        with open(path, "r", encoding="utf-8") as f:
            stylesheet = f.read()
            app.setStyleSheet(stylesheet)
            logger.info("Successfully loaded and applied stylesheet.")
    except (IOError, OSError) as e:
        # Catch potential file reading errors even if the file exists
        raise ThemeNotFoundError(f"Failed to read theme file at '{path}': {e}") from e


def main() -> None:
    """
    The main entry point for the Systemizer application.
    Initializes the application, loads styles, creates the main window, and starts the event loop.
    """
    logger.info("Starting Systemizer application...")
    app = QApplication(sys.argv)
    
    try:
        load_stylesheet(app)
    except ThemeNotFoundError as e:
        # Log a specific, actionable warning if the theme is missing.
        # The application can still run, but will lack custom styling.
        logger.warning(f"Could not load theme: {e}. Application will run with default styles.")

    try:
        window = MainWindow()
        window.show()
        logger.info("Main window displayed.")
        sys.exit(app.exec())
    except Exception as e:
        # A broad exception handler for any unexpected critical errors during startup.
        logger.critical(f"A critical error occurred, and the application must close: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
