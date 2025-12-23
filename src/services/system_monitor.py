import logging
import subprocess
import time
from typing import Dict, Any, List, Optional

import psutil

logger = logging.getLogger(__name__)

# --- Constants ---
BYTES_TO_GB = 1024 ** 3


class SystemMonitor:
    """
    A class to monitor core system metrics like CPU, RAM, Disk, and Network.

    This class centralizes all calls to the `psutil` library and provides
    a clean, cached interface for retrieving system information.
    """

    def __init__(self) -> None:
        """Initializes the SystemMonitor, caching static information."""
        self._boot_time: float = psutil.boot_time()
        self._total_mem_gb: float = psutil.virtual_memory().total / BYTES_TO_GB

        try:
            # Determine the primary disk path (C: on Windows, / on others)
            psutil.disk_usage('C:\\')
            self._disk_path: str = 'C:\\'
        except FileNotFoundError:
            self._disk_path: str = '/'

        self._ram_speed: str = self._fetch_ram_speed()

    def _fetch_ram_speed(self) -> str:
        """
        Fetches RAM speed using a PowerShell command on Windows.

        Returns:
            A string representing the RAM speed (e.g., "3200 MHz") or "N/A"
            if it cannot be determined.
        """
        try:
            cmd = 'powershell -Command "Get-CimInstance -ClassName Win32_PhysicalMemory | Select-Object -ExpandProperty Speed"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).decode().strip()
            
            # The command can return speeds for multiple RAM sticks. We'll use the first one.
            speeds: List[str] = [s for s in output.split('\n') if s.strip().isdigit()]
            
            if speeds:
                logger.info(f"Detected RAM speed: {speeds[0]} MHz")
                return f"{speeds[0]} MHz"

            logger.warning("Could not determine RAM speed from PowerShell output.")
            return "Unknown"
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to fetch RAM speed via PowerShell: {e}")
            return "N/A"
            
    def get_ram_speed_info(self) -> str:
        """Returns the cached RAM speed."""
        return self._ram_speed

    def get_cpu_stats(self) -> Dict[str, Any]:
        """
        Returns CPU usage percentage (total and per-core).

        Returns:
            A dictionary containing 'total_usage' (float) and 'per_core' (List[float]).
        """
        return {
            "total_usage": psutil.cpu_percent(interval=None),
            "per_core": psutil.cpu_percent(interval=None, percpu=True)
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Returns RAM and Swap usage statistics.

        Returns:
            A dictionary with RAM and Swap metrics in GB and percentage.
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total": self._total_mem_gb,
            "available": mem.available / BYTES_TO_GB,
            "used": mem.used / BYTES_TO_GB,
            "percent": mem.percent,
            "swap_total": swap.total / BYTES_TO_GB,
            "swap_used": swap.used / BYTES_TO_GB,
            "swap_percent": swap.percent
        }

    def get_disk_stats(self) -> Dict[str, Any]:
        """
        Returns disk usage for the primary partition.

        Returns:
            A dictionary with disk metrics in GB and percentage.
        """
        disk = psutil.disk_usage(self._disk_path)
        return {
            "total": disk.total / BYTES_TO_GB,
            "used": disk.used / BYTES_TO_GB,
            "percent": disk.percent
        }

    def get_network_stats(self) -> Dict[str, int]:
        """
        Returns total bytes sent and received since boot.

        Returns:
            A dictionary containing 'bytes_sent' and 'bytes_recv'.
        """
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        }

    def get_process_stats(self) -> int:
        """Returns the current number of running processes."""
        return len(psutil.pids())

    def get_uptime(self) -> float:
        """
        Returns the system uptime in seconds.

        Returns:
            The uptime in seconds as a float.
        """
        return time.time() - self._boot_time
