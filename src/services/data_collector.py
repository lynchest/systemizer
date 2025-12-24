from PySide6.QtCore import QThread, Signal
from src.services.system_monitor import SystemMonitor
from src.services.gpu_monitor import GPUMonitor
from src.settings import get_settings
import time


class DataCollectorThread(QThread):
    """Background thread for collecting system and GPU data without blocking UI."""
    
    # Signals for different update frequencies
    fast_update = Signal(dict)  # 1 second updates (CPU, RAM, Network)
    medium_update = Signal(dict)  # 5 second updates (Processes)
    slow_update = Signal(dict)  # 30 second updates (Disk, Uptime)
    gpu_update = Signal(dict)  # 1 second GPU updates (or disabled if no GPU)
    
    def __init__(self):
        super().__init__()
        self.sys_monitor = SystemMonitor()
        self.gpu_monitor = GPUMonitor()
        self.settings = get_settings()
        self.running = True
        self.tick_count = 0
        
        # Track which statistics are enabled
        self.enabled_stats = {}
        self._load_enabled_stats()
        
        # Check if GPU is available
        self.has_gpu = self.gpu_monitor._gpu_available
        
        # Network tracking for speed calculation
        net = self.sys_monitor.get_network_stats()
        self.last_net_recv = net['bytes_recv']
        self.last_net_sent = net['bytes_sent']
        
        # RAM Speed (fetched once)
        self.ram_speed = self.sys_monitor.get_ram_speed_info()
    
    def _load_enabled_stats(self):
        """Load which statistics are enabled from settings."""
        stats = self.settings.get_all_statistics()
        for stat_key, enabled in stats.items():
            self.enabled_stats[stat_key] = enabled
    
    def set_statistic_enabled(self, stat_key: str, enabled: bool):
        """Enable or disable a specific statistic."""
        self.enabled_stats[stat_key] = enabled
        print(f"[DataCollector] {stat_key} -> {enabled}")  # Debug için
    
    def force_refresh_all(self):
        """Force immediate refresh of all data."""
        fast_data = self._collect_fast_data()
        if fast_data:
            self.fast_update.emit(fast_data)
        
        medium_data = self._collect_medium_data()
        if medium_data:
            self.medium_update.emit(medium_data)
        
        slow_data = self._collect_slow_data()
        if slow_data:
            self.slow_update.emit(slow_data)
        
        gpu_data = self._collect_gpu_data()
        if gpu_data:
            self.gpu_update.emit(gpu_data)
        
    def run(self):
        """Main loop running in background thread."""
        while self.running:
            start_time = time.time()
            
            # Fast updates (every 1 second)
            fast_data = self._collect_fast_data()
            if fast_data:  # Only emit if there's data to send
                self.fast_update.emit(fast_data)
            
            # Medium updates (every 5 seconds)
            if self.tick_count % 5 == 0:
                medium_data = self._collect_medium_data()
                if medium_data:
                    self.medium_update.emit(medium_data)
            
            # Slow updates (every 30 seconds)
            if self.tick_count % 30 == 0:
                slow_data = self._collect_slow_data()
                if slow_data:
                    self.slow_update.emit(slow_data)
            
            # GPU updates (every 1 second if GPU exists, every 300 seconds to check for new GPU)
            if self.has_gpu or self.tick_count % 300 == 0:
                gpu_data = self._collect_gpu_data()
                if gpu_data:
                    self.gpu_update.emit(gpu_data)
                
                # Re-check if GPU became available
                if not self.has_gpu and gpu_data['available']:
                    self.has_gpu = True
            
            self.tick_count += 1
            
            # Sleep for remaining time to maintain 1 second interval
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)
    
    def _collect_fast_data(self):
        """Collect frequently changing data (CPU, RAM, Network)."""
        # Consolidated call for CPU and RAM
        cpu = self.sys_monitor.get_cpu_stats()
        ram = self.sys_monitor.get_memory_stats()
        
        # Network stats
        net = self.sys_monitor.get_network_stats()
        down_bytes = net['bytes_recv'] - self.last_net_recv
        up_bytes = net['bytes_sent'] - self.last_net_sent
        
        # Convert to KB/s for better precision
        down_speed = down_bytes / 1024  # KB/s
        up_speed = up_bytes / 1024  # KB/s
        
        # Update last values
        self.last_net_recv = net['bytes_recv']
        self.last_net_sent = net['bytes_sent']
        
        # Only include enabled statistics
        data = {}
        if self.enabled_stats.get('cpu', True):
            data['cpu_usage'] = cpu['total_usage']
        if self.enabled_stats.get('cpu_cores', True):
            data['cpu_cores'] = len(cpu['per_core'])
        if self.enabled_stats.get('ram', True):
            data['ram_percent'] = ram['percent']
            data['ram_used'] = ram['used']
            data['ram_total'] = ram['total']
        if self.enabled_stats.get('ram_speed', True):
            data['ram_speed'] = self.ram_speed
        if self.enabled_stats.get('net_down', True):
            data['net_down_speed'] = down_speed
        if self.enabled_stats.get('net_up', True):
            data['net_up_speed'] = up_speed
        
        return data if data else None
    
    def _collect_medium_data(self):
        """Collect moderately changing data (Processes)."""
        if not self.enabled_stats.get('processes', True):
            return None
            
        proc_count = self.sys_monitor.get_process_stats()
        return {
            'process_count': proc_count
        }
    
    def _collect_slow_data(self):
        """Collect slowly changing data (Disk, Uptime)."""
        data = {}
        
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
    
    def _collect_gpu_data(self):
        """Collect GPU data if available."""
        # Check if any GPU stats are enabled
        gpu_stats_enabled = any([
            self.enabled_stats.get('gpu', True),
            self.enabled_stats.get('vram', True),
            self.enabled_stats.get('gpu_temp', True),
            self.enabled_stats.get('gpu_power', True),
            self.enabled_stats.get('gpu_fan', True),
            self.enabled_stats.get('gpu_clock', True),
        ])
        
        # If all GPU stats are disabled, don't collect
        if not gpu_stats_enabled:
            return None
        
        gpu_stats = self.gpu_monitor.get_stats()
        
        if gpu_stats:
            data = {
                'available': True,
            }
            
            if self.enabled_stats.get('gpu', True):
                data['gpu_usage'] = gpu_stats['gpu_usage']
            if self.enabled_stats.get('vram', True):
                data['vram_used'] = int(gpu_stats['vram_used'] / 1024)  # GB
                data['vram_total'] = int(gpu_stats['vram_total'] / 1024) # GB
                data['vram_percent'] = gpu_stats['vram_percent']
            if self.enabled_stats.get('gpu_temp', True):
                data['temp'] = gpu_stats['temp']
            if self.enabled_stats.get('gpu_power', True):
                data['power_draw'] = int(gpu_stats['power_draw'])
            if self.enabled_stats.get('gpu_fan', True):
                data['fan_speed'] = gpu_stats['fan_speed']
            if self.enabled_stats.get('gpu_clock', True):
                data['core_clock'] = gpu_stats['core_clock']
            
            return data
        else:
            return {
                'available': False
            }
    
    def stop(self):
        """Stop the collection thread."""
        self.running = False
