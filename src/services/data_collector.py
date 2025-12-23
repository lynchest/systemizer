import time
from typing import Dict, Any, Optional

from PySide6.QtCore import QThread, Signal

from src.services.gpu_monitor import GPUMonitor
from src.services.system_monitor import SystemMonitor
from src.settings import Settings

# Constants for update intervals in seconds
# Makes the code more readable and easier to change.
FAST_UPDATE_INTERVAL_S = 1
MEDIUM_UPDATE_INTERVAL_S = 5
SLOW_UPDATE_INTERVAL_S = 30
GPU_RECHECK_INTERVAL_S = 300


class DataCollectorThread(QThread):
    """
    Background thread for collecting system and GPU data without blocking the UI.

    This thread uses different update frequencies for various metrics to optimize performance.
    - Fast (1s): CPU, RAM, Network (high volatility)
    - Medium (5s): Process Count
    - Slow (30s): Disk Usage, Uptime
    - GPU (1s): GPU metrics (if available)

    Attributes:
        fast_update (Signal): Emits frequently updated data.
        medium_update (Signal): Emits moderately updated data.
        slow_update (Signal): Emits slowly updated data.
        gpu_update (Signal): Emits GPU-specific data.
    """

    fast_update = Signal(dict)
    medium_update = Signal(dict)
    slow_update = Signal(dict)
    gpu_update = Signal(dict)

    def __init__(self, settings: Settings, parent=None):
        """
        Initializes the DataCollectorThread.

        Args:
            settings (Settings): The application settings object. This is dependency-injected
                                 to improve testability and reduce coupling.
            parent: Optional parent for the QThread.
        """
        super().__init__(parent)
        self.settings = settings
        self.sys_monitor = SystemMonitor()
        self.gpu_monitor = GPUMonitor()

        self.running: bool = True
        self._tick_count: int = 0
        self.enabled_stats: Dict[str, bool] = {}
        self._load_enabled_stats()

        self.has_gpu: bool = self.gpu_monitor.is_gpu_available()

        # Initialize network tracking for speed calculation
        net_stats = self.sys_monitor.get_network_stats()
        self._last_net_recv: int = net_stats['bytes_recv']
        self._last_net_sent: int = net_stats['bytes_sent']

        # RAM speed is fetched once as it doesn't change during runtime
        self.ram_speed: str = self.sys_monitor.get_ram_speed_info()

    def _load_enabled_stats(self) -> None:
        """Loads which statistics are enabled from the settings object."""
        self.enabled_stats = self.settings.get_all_statistics()

    def set_statistic_enabled(self, stat_key: str, enabled: bool) -> None:
        """Enables or disables a specific statistic."""
        self.enabled_stats[stat_key] = enabled

    def run(self) -> None:
        """Main loop running in the background thread."""
        while self.running:
            start_time = time.time()

            if fast_data := self._collect_fast_data():
                self.fast_update.emit(fast_data)

            if self._tick_count % MEDIUM_UPDATE_INTERVAL_S == 0:
                if medium_data := self._collect_medium_data():
                    self.medium_update.emit(medium_data)

            if self._tick_count % SLOW_UPDATE_INTERVAL_S == 0:
                if slow_data := self._collect_slow_data():
                    self.slow_update.emit(slow_data)

            if self.has_gpu or self._tick_count % GPU_RECHECK_INTERVAL_S == 0:
                if gpu_data := self._collect_gpu_data():
                    self.gpu_update.emit(gpu_data)
                    if not self.has_gpu and gpu_data.get('available', False):
                        self.has_gpu = True

            self._tick_count += 1
            self._sleep_to_maintain_interval(start_time)

    def _sleep_to_maintain_interval(self, start_time: float) -> None:
        """Calculates and sleeps for the remaining time to maintain a 1-second interval."""
        elapsed = time.time() - start_time
        sleep_time = max(0, FAST_UPDATE_INTERVAL_S - elapsed)
        time.sleep(sleep_time)

    def stop(self) -> None:
        """Stops the collection thread."""
        self.running = False
        self.wait()  # Wait for the thread to finish cleanly

    def _collect_fast_data(self) -> Optional[Dict[str, Any]]:
        """Collects frequently changing data (CPU, RAM, Network)."""
        data: Dict[str, Any] = {}
        
        # Network speed calculation must happen before fetching latest stats
        down_speed, up_speed = self._calculate_network_speed()
        
        if self.enabled_stats.get('net_down', True):
            data['net_down_speed'] = down_speed
        if self.enabled_stats.get('net_up', True):
            data['net_up_speed'] = up_speed

        if self.enabled_stats.get('cpu', True) or self.enabled_stats.get('cpu_cores', True):
            cpu_stats = self.sys_monitor.get_cpu_stats()
            if self.enabled_stats.get('cpu', True):
                data['cpu_usage'] = cpu_stats['total_usage']
            if self.enabled_stats.get('cpu_cores', True):
                data['cpu_cores'] = len(cpu_stats['per_core'])
        
        if self.enabled_stats.get('ram', True):
            ram_stats = self.sys_monitor.get_memory_stats()
            data['ram_percent'] = ram_stats['percent']
            data['ram_used'] = ram_stats['used']
            data['ram_total'] = ram_stats['total']

        if self.enabled_stats.get('ram_speed', True):
            data['ram_speed'] = self.ram_speed

        return data if data else None

    def _calculate_network_speed(self) -> (float, float):
        """Calculates network download and upload speed in MB/s."""
        net = self.sys_monitor.get_network_stats()
        # Convert bytes to MB
        bytes_to_mb = 1024 * 1024

        down_speed = (net['bytes_recv'] - self._last_net_recv) / bytes_to_mb
        up_speed = (net['bytes_sent'] - self._last_net_sent) / bytes_to_mb

        self._last_net_recv = net['bytes_recv']
        self._last_net_sent = net['bytes_sent']

        return down_speed, up_speed

    def _collect_medium_data(self) -> Optional[Dict[str, Any]]:
        """Collects moderately changing data (Processes)."""
        if not self.enabled_stats.get('processes', True):
            return None

        return {'process_count': self.sys_monitor.get_process_stats()}

    def _collect_slow_data(self) -> Optional[Dict[str, Any]]:
        """Collects slowly changing data (Disk, Uptime)."""
        data: Dict[str, Any] = {}
        
        if self.enabled_stats.get('disk', True):
            disk = self.sys_monitor.get_disk_stats()
            data['disk_percent'] = disk['percent']
        
        if self.enabled_stats.get('uptime', True):
            uptime_sec = self.sys_monitor.get_uptime()
            hours = int(uptime_sec // 3600)
            minutes = int((uptime_sec % 3600) // 60)
            data['uptime_hours'] = hours
            data['uptime_minutes'] = minutes
        
        return data if data else None

    def _collect_gpu_data(self) -> Optional[Dict[str, Any]]:
        """Collects GPU data if available and if any GPU stat is enabled."""
        gpu_stats_enabled = any(
            self.enabled_stats.get(key, True) for key in
            ['gpu', 'vram', 'gpu_temp', 'gpu_power', 'gpu_fan', 'gpu_clock']
        )

        if not gpu_stats_enabled:
            return None

        gpu_stats = self.gpu_monitor.get_stats()

        if not gpu_stats:
            return {'available': False}

        # Helper to avoid repetition
        def get_stat(key, default=None):
            return gpu_stats.get(key, default)

        data: Dict[str, Any] = {'available': True}
        
        if self.enabled_stats.get('gpu', True):
            data['gpu_usage'] = get_stat('gpu_usage')
        if self.enabled_stats.get('vram', True):
            # Convert MB to GB for display
            data['vram_used'] = int(get_stat('vram_used', 0) / 1024)
            data['vram_total'] = int(get_stat('vram_total', 0) / 1024)
            data['vram_percent'] = get_stat('vram_percent')
        if self.enabled_stats.get('gpu_temp', True):
            data['temp'] = get_stat('temp')
        if self.enabled_stats.get('gpu_power', True):
            data['power_draw'] = int(get_stat('power_draw', 0))
        if self.enabled_stats.get('gpu_fan', True):
            data['fan_speed'] = get_stat('fan_speed')
        if self.enabled_stats.get('gpu_clock', True):
            data['core_clock'] = get_stat('core_clock')
            
        return data
