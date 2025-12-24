import requests
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Callable
import logging
from src.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VersionChecker:
    """Checks for application updates from GitHub releases."""
    
    _instance = None
    _initialized = False
    
    GITHUB_REPO = "lynchest/systemizer"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VersionChecker, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Get current version from settings
            settings = get_settings()
            self.current_version = settings.get_application_version()
            self.latest_version = None
            self.update_available = False
            self.last_check_time = None
            self.check_interval = timedelta(hours=24)
            self.update_callbacks = []
            self.github_releases_url = "https://github.com/lynchest/systemizer/releases"
            self._initialized = True
            
            logger.info(f"Version Checker initialized with app version: {self.current_version}")
    
    def set_current_version(self, version: str):
        """Manually set the current application version and save to settings."""
        settings = get_settings()
        settings.set_application_version(version)
        self.current_version = version
        logger.info(f"Set application version: {version}")
    
    def register_callback(self, callback: Callable[[bool, Optional[str]], None]):
        """Register a callback to be called when update check completes."""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _notify_callbacks(self, update_available: bool, latest_version: Optional[str]):
        """Notify all registered callbacks."""
        for callback in self.update_callbacks:
            try:
                callback(update_available, latest_version)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def check_for_updates_async(self, callback=None):
        """Check for updates in background thread."""
        if callback:
            self.register_callback(callback)
        
        thread = threading.Thread(target=self.check_for_updates, daemon=True)
        thread.start()
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check if application updates are available from GitHub releases.
        Returns: (update_available, latest_version)
        """
        # Check if enough time has passed since last check
        if self.last_check_time and datetime.now() - self.last_check_time < self.check_interval:
            logger.debug(f"Skipping update check (last checked {(datetime.now() - self.last_check_time).total_seconds()} seconds ago)")
            self._notify_callbacks(self.update_available, self.latest_version)
            return self.update_available, self.latest_version
        
        try:
            logger.info("Checking for application updates from GitHub...")
            latest = self._fetch_latest_version()
            
            self.latest_version = latest
            self.last_check_time = datetime.now()
            
            # Compare versions
            if latest and self.current_version:
                self.update_available = self._compare_versions(
                    self.current_version, 
                    latest
                )
                if self.update_available:
                    logger.info(f"Update available: {self.current_version} -> {latest}")
                else:
                    logger.info(f"Application is up to date: {self.current_version}")
            
            self._notify_callbacks(self.update_available, latest)
            return self.update_available, latest
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            self._notify_callbacks(False, None)
            return False, None
    
    def _fetch_latest_version(self) -> Optional[str]:
        """Fetch the latest version from GitHub releases API."""
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Systemizer-App'
            }
            
            response = requests.get(
                self.GITHUB_API_URL,
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract version from tag_name (e.g., "v1.2.3" -> "1.2.3")
                tag_name = data.get('tag_name', '')
                version = tag_name.lstrip('v')
                
                if version:
                    logger.info(f"Latest version on GitHub: {version}")
                    return version
            else:
                logger.warning(f"GitHub API returned status code: {response.status_code}")
            
            return None
            
        except requests.exceptions.Timeout:
            logger.warning("Timeout while checking for updates")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error while checking for updates")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch latest version: {e}")
            return None
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """
        Compare two version strings.
        Returns True if update is available (latest > current).
        Handles formats like "1.2.3" or "1.2.3.4"
        """
        try:
            # Parse versions
            current_parts = [int(x) for x in current.split('.') if x.isdigit()]
            latest_parts = [int(x) for x in latest.split('.') if x.isdigit()]
            
            # Pad with zeros
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            
            # Compare
            for c, l in zip(current_parts, latest_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            
            return False
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return False
    
    def get_update_info(self) -> Dict:
        """Get current application update information."""
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "releases_url": self.github_releases_url
        }
    
    def force_check(self):
        """Force an immediate update check, ignoring the interval."""
        self.last_check_time = None
        return self.check_for_updates()
    
    def get_releases_url(self) -> str:
        """Get the GitHub releases page URL."""
        return self.github_releases_url
    
    def open_releases_page(self):
        """Open the GitHub releases page in default browser."""
        try:
            import webbrowser
            webbrowser.open(self.github_releases_url)
            logger.info(f"Opened releases page: {self.github_releases_url}")
        except Exception as e:
            logger.error(f"Failed to open releases page: {e}")
