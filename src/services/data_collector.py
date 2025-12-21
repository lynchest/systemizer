from PySide6.QtCore import QThread, Signal
from src.services.system_monitor import SystemMonitor
from src.services.gpu_monitor import GPUMonitor
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
        self.running = True
        self.tick_count = 0
        
        # Check if GPU is available
        self.has_gpu = self.gpu_monitor._handle is not None
        
        # Network tracking for speed calculation
        net = self.sys_monitor.get_network_stats()
        self.last_net_recv = net['bytes_recv']
        self.last_net_sent = net['bytes_sent']
        
        # RAM Speed (fetched once)
        self.ram_speed = self.sys_monitor.get_ram_speed_info()
        
    def run(self):
        """Main loop running in background thread."""
        while self.running:
            start_time = time.time()
            
            # Fast updates (every 1 second)
            fast_data = self._collect_fast_data()
            self.fast_update.emit(fast_data)
            
            # Medium updates (every 5 seconds)
            if self.tick_count % 5 == 0:
                medium_data = self._collect_medium_data()
                self.medium_update.emit(medium_data)
            
            # Slow updates (every 30 seconds)
            if self.tick_count % 30 == 0:
                slow_data = self._collect_slow_data()
                self.slow_update.emit(slow_data)
            
            # GPU updates (every 1 second if GPU exists, every 300 seconds to check for new GPU)
            if self.has_gpu or self.tick_count % 300 == 0:
                gpu_data = self._collect_gpu_data()
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
        down_speed = (net['bytes_recv'] - self.last_net_recv) / 1024 / 1024  # MB/s
        up_speed = (net['bytes_sent'] - self.last_net_sent) / 1024 / 1024  # MB/s
        
        # Update last values
        self.last_net_recv = net['bytes_recv']
        self.last_net_sent = net['bytes_sent']
        
        return {
            'cpu_usage': cpu['total_usage'],
            'cpu_cores': len(cpu['per_core']),
            'ram_percent': ram['percent'],
            'ram_used': ram['used'],
            'ram_total': ram['total'],
            'ram_speed': self.ram_speed,
            'net_down_speed': down_speed,
            'net_up_speed': up_speed
        }
    
    def _collect_medium_data(self):
        """Collect moderately changing data (Processes)."""
        proc_count = self.sys_monitor.get_process_stats()
        return {
            'process_count': proc_count
        }
    
    def _collect_slow_data(self):
        """Collect slowly changing data (Disk, Uptime)."""
        disk = self.sys_monitor.get_disk_stats()
        uptime_sec = self.sys_monitor.get_uptime()
        hours = int(uptime_sec // 3600)
        minutes = int((uptime_sec % 3600) // 60)
        
        return {
            'disk_percent': disk['percent'],
            'uptime_hours': hours,
            'uptime_minutes': minutes
        }
    
    def _collect_gpu_data(self):
        """Collect GPU data if available."""
        gpu_stats = self.gpu_monitor.get_stats()
        
        if gpu_stats:
            return {
                'available': True,
                'gpu_usage': gpu_stats['gpu_usage'],
                'vram_used': int(gpu_stats['vram_used'] / 1024),  # GB
                'vram_total': int(gpu_stats['vram_total'] / 1024), # GB
                'vram_percent': gpu_stats['vram_percent'],
                'temp': gpu_stats['temp'],
                'power_draw': int(gpu_stats['power_draw']),
                'fan_speed': gpu_stats['fan_speed'],
                'core_clock': gpu_stats['core_clock']
            }
        else:
            return {
                'available': False
            }
    
    def stop(self):
        """Stop the collection thread."""
        self.running = False
