import json
import os
from pathlib import Path


class Settings:
    """Manages user preferences and settings for Systemizer."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "statistics": {
            "cpu": True,
            "ram": True,
            "gpu": True,
            "vram": True,
            "gpu_temp": True,
            "gpu_power": True,
            "gpu_fan": True,
            "gpu_clock": True,
            "disk": True,
            "net_down": True,
            "net_up": True,
            "processes": True,
            "uptime": True,
            "cpu_cores": True,
            "ram_speed": True,
        },
        "theme": {
            "background_main": "#0d0d0d",     # Pure Black
        },
        "gpu_updates": {
            "check_enabled": True,
            "check_interval_hours": 24,
            "notify_on_update": True,
        }
    }
    
    # Modern color palette for background selection
    BACKGROUND_COLORS = {
        "Pure Black": "#0d0d0d",
        "Very Dark Gray": "#1a1a1a",
        "Dark Gray": "#2a2a2a",
        "Dark Red": "#3a1a1a",
        "Dark Blue": "#1a2a3a",
        "Dark Green": "#1a3a1a",
        "Dark Purple": "#2a1a3a",
        "Dark Brown": "#3a2a1a",
        "Catppuccin Dark": "#1e1e2e",
    }
    
    def __init__(self):
        self.settings_dir = Path.home() / ".systemizer"
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = self.DEFAULT_SETTINGS.copy()
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file if it exists."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge loaded settings with defaults
                    self.settings["statistics"].update(loaded.get("statistics", {}))
                    self.settings["theme"].update(loaded.get("theme", {}))
                    self.settings["gpu_updates"].update(loaded.get("gpu_updates", {}))
            else:
                self._save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value by key (supports dot notation: 'statistics.cpu')."""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set_setting(self, key: str, value):
        """Set a setting value by key (supports dot notation: 'statistics.cpu')."""
        keys = key.split('.')
        target = self.settings
        
        # Navigate to the right place
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # Set the value
        target[keys[-1]] = value
        self._save_settings()
    
    def get_all_statistics(self):
        """Get all statistics settings."""
        return self.settings.get("statistics", {})
    
    def set_statistic(self, stat_name: str, enabled: bool):
        """Enable or disable a specific statistic."""
        self.set_setting(f"statistics.{stat_name}", enabled)
    
    def is_statistic_enabled(self, stat_name: str) -> bool:
        """Check if a statistic is enabled."""
        return self.get_setting(f"statistics.{stat_name}", True)
    
    def get_theme_color(self, color_key: str) -> str:
        """Get a theme color value."""
        return self.get_setting(f"theme.{color_key}", self.DEFAULT_SETTINGS["theme"].get(color_key, "#1e1e2e"))
    
    def set_theme_color(self, color_key: str, color_value: str):
        """Set a theme color value."""
        self.set_setting(f"theme.{color_key}", color_value)
    
    def get_all_theme_colors(self) -> dict:
        """Get all theme colors."""
        return self.settings.get("theme", self.DEFAULT_SETTINGS["theme"].copy())


# Global settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
