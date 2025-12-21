import psutil

class SystemMonitor:
    def __init__(self):
        self._boot_time = psutil.boot_time()
        self._total_mem = psutil.virtual_memory().total / 1024**3
        
        # Cache disk path
        try:
            psutil.disk_usage('C:\\')
            self._disk_path = 'C:\\'
        except:
            self._disk_path = '/'
            
        # Get RAM speed (MHz) - Only once on startup
        self._ram_speed = self._get_ram_speed()

    def _get_ram_speed(self):
        """Fetches RAM speed using PowerShell on Windows."""
        try:
            import subprocess
            # Use PowerShell to get RAM speed (more reliable than wmic on modern Windows)
            cmd = 'powershell -Command "Get-CimInstance -ClassName Win32_PhysicalMemory | Select-Object -ExpandProperty Speed"'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            
            # Output might be multiple lines if there are multiple sticks
            speeds = [s.strip() for s in output.split('\n') if s.strip() and s.strip().isdigit()]
            
            if speeds:
                return f"{speeds[0]} MHz"
            return "Unknown"
        except:
            return "N/A"
            
    def get_ram_speed_info(self):
        """Returns the cached RAM speed."""
        return self._ram_speed

    def get_cpu_stats(self):
        """Returns CPU usage percentage and per-core usage."""
        cpu_percent = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        return {
            "total_usage": cpu_percent,
            "per_core": per_core
        }

    def get_memory_stats(self):
        """Returns RAM and Swap usage stats in one consolidated call."""
        # Consolidated call - virtual_memory and swap_memory are separate
        # but we can get them together to cache the data
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total": self._total_mem,
            "available": mem.available / 1024**3,
            "used": mem.used / 1024**3,
            "percent": mem.percent,
            "swap_total": swap.total / 1024**3,
            "swap_used": swap.used / 1024**3,
            "swap_percent": swap.percent
        }

    def get_disk_stats(self):
        """Returns Disk usage for the main partition."""
        disk = psutil.disk_usage(self._disk_path)
        return {
            "total": disk.total / 1024**3, # GB
            "used": disk.used / 1024**3, 
            "percent": disk.percent
        }

    def get_network_stats(self):
        """Returns bytes sent/recv."""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        }

    def get_process_stats(self):
        """Returns number of running processes."""
        return len(psutil.pids())

    def get_uptime(self):
        """Returns system uptime in seconds."""
        import time
        return time.time() - self._boot_time
