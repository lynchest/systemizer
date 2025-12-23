import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Settings:
    """
    Manages user preferences and settings for the Systemizer application.

    This class handles loading settings from a JSON file, saving changes,
    and providing default values if the file doesn't exist or is corrupt.
    It uses a singleton pattern via the `get_settings` function to ensure
    a single configuration state throughout the application.

    Attributes:
        DEFAULT_SETTINGS (Dict[str, Any]): A dictionary of default settings.
        BACKGROUND_COLORS (Dict[str, str]): A palette of available background colors.
    """

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "statistics": {
            "cpu": True, "ram": True, "gpu": True, "vram": True,
            "gpu_temp": True, "gpu_power": True, "gpu_fan": True,
            "gpu_clock": True, "disk": True, "net_down": True,
            "net_up": True, "processes": True, "uptime": True,
            "cpu_cores": True, "ram_speed": True,
        },
        "theme": {
            "background_main": "#1e1e2e",  # Catppuccin Dark
        }
    }

    BACKGROUND_COLORS: Dict[str, str] = {
        "Catppuccin": "#1e1e2e",
        "Pure Black": "#0d0d0d",
        "Dark Gray": "#2a2a2a",
        "Dark Blue": "#1a2a3a",
        "Dark Green": "#1a3a1a",
        "Dark Purple": "#2a1a3a",
    }

    def __init__(self) -> None:
        """Initializes the Settings object."""
        self.settings_dir: Path = Path.home() / ".systemizer"
        self.settings_file: Path = self.settings_dir / "settings.json"
        self.settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self._load_settings()

    def _load_settings(self) -> None:
        """
        Loads settings from the JSON file.
        If the file doesn't exist or is invalid, it creates one with default settings.
        """
        if not self.settings_file.exists():
            self._save_settings()
            return

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Merge loaded settings with defaults to ensure all keys are present
                self.settings["statistics"].update(loaded_settings.get("statistics", {}))
                self.settings["theme"].update(loaded_settings.get("theme", {}))
                logger.info("Settings loaded successfully from %s", self.settings_file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error loading settings file: %s. Reverting to default settings.", e)
            self.settings = self.DEFAULT_SETTINGS.copy()
            self._save_settings()  # Attempt to fix the corrupt file

    def _save_settings(self) -> None:
        """Saves the current settings to the JSON file."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved to %s", self.settings_file)
        except (IOError, OSError) as e:
            logger.error("Error saving settings to file: %s", e)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Gets a setting value by key, supporting dot notation.

        Args:
            key: The key of the setting (e.g., 'statistics.cpu').
            default: The value to return if the key is not found.

        Returns:
            The value of the setting or the default value.
        """
        try:
            keys = key.split('.')
            value = self.settings
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_setting(self, key: str, value: Any) -> None:
        """
        Sets a setting value by key, supporting dot notation.

        Args:
            key: The key of the setting (e.g., 'statistics.cpu').
            value: The new value to set.
        """
        keys = key.split('.')
        target = self.settings
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        
        target[keys[-1]] = value
        self._save_settings()

    def get_all_statistics(self) -> Dict[str, bool]:
        """Returns the entire dictionary of statistics settings."""
        return self.settings.get("statistics", {})

    def is_statistic_enabled(self, stat_name: str) -> bool:
        """
        Checks if a specific statistic is enabled.

        Args:
            stat_name: The name of the statistic to check.

        Returns:
            True if the statistic is enabled, False otherwise.
        """
        return self.get_setting(f"statistics.{stat_name}", True)

    def get_theme_color(self, color_key: str) -> str:
        """
        Gets a theme color by its key.

        Args:
            color_key: The key of the color (e.g., 'background_main').

        Returns:
            The hex color value as a string.
        """
        default_color = self.DEFAULT_SETTINGS["theme"].get(color_key, "#1e1e2e")
        return self.get_setting(f"theme.{color_key}", default_color)

    def set_theme_color(self, color_key: str, color_value: str) -> None:
        """
        Sets a theme color.

        Args:
            color_key: The key of the color.
            color_value: The new hex color value.
        """
        self.set_setting(f"theme.{color_key}", color_value)


# --- Singleton Instance ---
_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Provides access to the global Settings instance.

    This function implements a singleton pattern to ensure that there is only
    one instance of the Settings class throughout the application's lifecycle.

    Returns:
        The single, shared instance of the Settings class.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
