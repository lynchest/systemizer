import subprocess
import json
import threading
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUDriverUpdater:
    """Monitors and checks GPU driver updates for NVIDIA and AMD."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPUDriverUpdater, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.gpu_vendor = "Unknown"
            self.current_driver_version = None
            self.latest_driver_version = None
            self.driver_update_available = False
            self.last_check_time = None
            self.check_interval = timedelta(hours=24)
            self.update_callbacks = []
            self._initialized = True
            
            # Initial detection
            self._detect_driver_version()
    
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
    
    def _detect_driver_version(self) -> Optional[str]:
        """Detect installed GPU driver version."""
        try:
            # First try NVIDIA
            nvidia_version = self._get_nvidia_driver_version()
            if nvidia_version:
                self.gpu_vendor = "NVIDIA"
                self.current_driver_version = nvidia_version
                logger.info(f"Detected NVIDIA GPU with driver version {nvidia_version}")
                return nvidia_version
            
            # Then try AMD
            amd_version = self._get_amd_driver_version()
            if amd_version:
                self.gpu_vendor = "AMD"
                self.current_driver_version = amd_version
                logger.info(f"Detected AMD GPU with driver version {amd_version}")
                return amd_version
            
            # Try Intel
            intel_version = self._get_intel_driver_version()
            if intel_version:
                self.gpu_vendor = "Intel"
                self.current_driver_version = intel_version
                logger.info(f"Detected Intel GPU with driver version {intel_version}")
                return intel_version
                
        except Exception as e:
            logger.error(f"Error detecting driver version: {e}")
        
        return None
    
    def _get_nvidia_driver_version(self) -> Optional[str]:
        """Get NVIDIA driver version using nvidia-smi."""
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                timeout=5,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            return output if output else None
        except Exception as e:
            logger.debug(f"Failed to get NVIDIA driver version: {e}")
            return None
    
    def _get_amd_driver_version(self) -> Optional[str]:
        """Get AMD driver version from registry or system info."""
        try:
            # Try PowerShell to get AMD driver info
            cmd = 'powershell -NoProfile -Command "Get-ItemProperty -Path \'HKLM:\\SOFTWARE\\AMD\\ATI.ACE\\Core-Static\' -Name DriverVersion -ErrorAction SilentlyContinue | Select-Object -ExpandProperty DriverVersion"'
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                timeout=5,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            if output:
                return output
            
            # Fallback: Try WMI for AMD/Radeon devices
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PnPSignedDriver -Filter \\"DeviceName LIKE \'%AMD%\' OR DeviceName LIKE \'%Radeon%\'\\" | Select-Object -ExpandProperty DriverVersion | Select-Object -First 1"'
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                timeout=5,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            return output if output else None
        except Exception as e:
            logger.debug(f"Failed to get AMD driver version: {e}")
            return None
    
    def _get_intel_driver_version(self) -> Optional[str]:
        """Get Intel GPU driver version."""
        try:
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PnPSignedDriver -Filter \\"DeviceName LIKE \'%Intel%Graphics%\'\\" | Select-Object -ExpandProperty DriverVersion | Select-Object -First 1"'
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                timeout=5,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            return output if output else None
        except Exception as e:
            logger.debug(f"Failed to get Intel driver version: {e}")
            return None
    
    def check_for_updates_async(self, callback=None):
        """Check for driver updates in background thread."""
        if callback:
            self.register_callback(callback)
        
        thread = threading.Thread(target=self.check_for_updates, daemon=True)
        thread.start()
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check if GPU driver updates are available.
        Returns: (update_available, latest_version)
        """
        # Check if enough time has passed since last check
        if self.last_check_time and datetime.now() - self.last_check_time < self.check_interval:
            logger.debug(f"Skipping update check (last checked {(datetime.now() - self.last_check_time).total_seconds()} seconds ago)")
            self._notify_callbacks(self.driver_update_available, self.latest_driver_version)
            return self.driver_update_available, self.latest_driver_version
        
        try:
            logger.info(f"Checking for {self.gpu_vendor} driver updates...")
            
            if self.gpu_vendor == "NVIDIA":
                latest = self._check_nvidia_updates()
            elif self.gpu_vendor == "AMD":
                latest = self._check_amd_updates()
            elif self.gpu_vendor == "Intel":
                latest = self._check_intel_updates()
            else:
                latest = None
            
            self.latest_driver_version = latest
            self.last_check_time = datetime.now()
            
            # Compare versions
            if latest and self.current_driver_version:
                self.driver_update_available = self._compare_versions(
                    self.current_driver_version, 
                    latest
                )
                if self.driver_update_available:
                    logger.info(f"Update available: {self.current_driver_version} -> {latest}")
                else:
                    logger.info(f"Driver is up to date: {self.current_driver_version}")
            
            self._notify_callbacks(self.driver_update_available, latest)
            return self.driver_update_available, latest
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            self._notify_callbacks(False, None)
            return False, None
    
    def _check_nvidia_updates(self) -> Optional[str]:
        """Check NVIDIA's official driver page for latest version."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Try NVIDIA's driver API
            response = requests.get(
                "https://api.nvidia.com/download/checkDriverVersion",
                params={
                    "psid": 95,      # Windows 10/11
                    "pfid": 911,     # GeForce Desktop
                    "osID": 57,      # Windows 64-bit
                    "dch": 1
                },
                timeout=5,
                headers=headers
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get("DriverVersion")
                except:
                    pass
            
            return None
        except Exception as e:
            logger.debug(f"Failed to check NVIDIA updates: {e}")
            return None
    
    def _check_amd_updates(self) -> Optional[str]:
        """Check AMD's driver version through web scraping or API."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Try to get AMD driver info (simplified approach)
            # AMD doesn't have a public JSON API, so this is a simplified check
            response = requests.get(
                "https://www.amd.com/en/support/amd-driver-and-support-releases",
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 200:
                # Look for version patterns in the HTML
                import re
                # Match patterns like "24.1.1" or "23.12"
                pattern = r'(\d+\.\d+(?:\.\d+)?)'
                matches = re.findall(pattern, response.text)
                
                if matches:
                    # Return the first (likely latest) match
                    return matches[0]
            
            return None
        except Exception as e:
            logger.debug(f"Failed to check AMD updates: {e}")
            return None
    
    def _check_intel_updates(self) -> Optional[str]:
        """Check Intel GPU driver version from Intel's download center or Windows Update."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Try to check Intel's driver page for latest version
            # Intel typically provides drivers through Windows Update or Intel Download Center
            response = requests.get(
                "https://www.intel.com/content/www/us/en/support/intel-graphics.html",
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 200:
                import re
                # Look for version patterns in the HTML
                # Intel driver versions are typically in format like "31.0.101.5034" or "27.20.100.9316"
                pattern = r'(\d+\.\d+\.\d+\.\d+)'
                matches = re.findall(pattern, response.text)
                
                if matches:
                    # Return the first match (usually latest)
                    # Filter out dates and other numbers
                    for match in matches:
                        parts = match.split('.')
                        if len(parts) == 4 and int(parts[0]) < 100:  # Intel drivers typically have first digit < 100
                            return match
            
            # Fallback: Try to get from Windows Device Manager via WMI
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PnPSignedDriver -Filter \\"DeviceName LIKE \'%Intel%Graphics%\'\\" | Select-Object -First 1 DriverVersion"'
            try:
                output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
                if output and 'DriverVersion' not in output:
                    return output
            except:
                pass
            
            return None
        except Exception as e:
            logger.debug(f"Failed to check Intel updates: {e}")
            return None
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """
        Compare two version strings.
        Returns True if update is available (latest > current).
        """
        try:
            # Parse versions (handles format like "536.23" or "23.2.1")
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
        """Get current driver update information."""
        return {
            "vendor": self.gpu_vendor,
            "current_version": self.current_driver_version,
            "latest_version": self.latest_driver_version,
            "update_available": self.driver_update_available,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }
    
    def force_check(self):
        """Force an immediate update check, ignoring the interval."""
        self.last_check_time = None
        return self.check_for_updates()
