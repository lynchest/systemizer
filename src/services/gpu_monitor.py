import pynvml
import subprocess
import json
import os

try:
    from pyadl import ADLManager
    HAS_PYADL = True
except:
    HAS_PYADL = False

class GPUMonitor:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPUMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._gpu_available = False
            self.vendor = "Unknown"
            self.gpu_name = "Detecting..."
            self.vram_total = 0 # MB
            self._handle = None # NVML Handle
            self._adl_device = None # ADL Handle
            
            # 1. Try to detect vendor first
            self.vendor = self._detect_vendor()
            
            # 2. Initialize based on vendor
            if self.vendor == "NVIDIA":
                self._init_nvidia()
            elif self.vendor == "AMD":
                self._init_amd()
            
            # 3. Fallback if vendor specific init failed
            if not self._gpu_available:
                self._init_generic()
                
            self._initialized = True

    def _detect_vendor(self):
        """Detect GPU vendor using PowerShell."""
        try:
            cmd = 'powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Caption | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if not output: return "Unknown"
            
            data = json.loads(output)
            if isinstance(data, list):
                data = data[0]
            
            name = data.get("Caption", "").upper()
            if "NVIDIA" in name: return "NVIDIA"
            if "AMD" in name or "RADEON" in name: return "AMD"
            if "INTEL" in name: return "Intel"
            return "Generic"
        except:
            return "Unknown"

    def _init_nvidia(self):
        """Initialize NVIDIA monitoring using NVML."""
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(self._handle)
                self.gpu_name = name.decode('utf-8') if isinstance(name, bytes) else name
                
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
                self.vram_total = mem_info.total / 1024**2 # MB
                self._gpu_available = True
        except:
            self._gpu_available = False

    def _init_amd(self):
        """Initialize AMD monitoring using pyadl."""
        if HAS_PYADL:
            try:
                adls = ADLManager.getInstance().getDevices()
                if adls:
                    self._adl_device = adls[0]
                    self.gpu_name = self._adl_device.adapterName
                    self._gpu_available = True
                    return
            except:
                pass
        
        # Fallback to generic detection if pyadl fails
        self._init_generic()

    def _init_generic(self):
        """Fallback to PowerShell for basic GPU info."""
        try:
            cmd = 'powershell -Command "Get-CimInstance Win32_VideoController | Select-Object -First 1 Caption, AdapterRAM | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if output:
                data = json.loads(output)
                self.gpu_name = data.get("Caption", "Generic GPU")
                ram_bytes = data.get("AdapterRAM", 0)
                if ram_bytes:
                    self.vram_total = int(ram_bytes) / 1024**2
                self._gpu_available = True
        except:
            self.gpu_name = "No GPU Detected"
            self._gpu_available = False

    def get_stats(self):
        """Returns a dict of current GPU stats."""
        if not self._gpu_available:
            return None

        if self.vendor == "NVIDIA" and self._handle:
            return self._get_nvidia_stats()
        elif self.vendor == "AMD":
            return self._get_amd_stats()
        else:
            return self._get_generic_stats()

    def _get_nvidia_stats(self):
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            temp = pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU)
            
            try:
                power = pynvml.nvmlDeviceGetPowerUsage(self._handle) / 1000.0
            except: power = 0
            
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(self._handle)
            except: fan = 0
            
            core_clock = pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_GRAPHICS)
            mem_clock = pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_MEM)

            vram_used = mem_info.used / 1024**2
            
            return {
                "name": self.gpu_name,
                "gpu_usage": util.gpu,
                "vram_total": self.vram_total,
                "vram_used": vram_used,
                "vram_percent": (vram_used / self.vram_total) * 100 if self.vram_total > 0 else 0,
                "temp": temp,
                "power_draw": power,
                "fan_speed": fan,
                "core_clock": core_clock,
                "memory_clock": mem_clock
            }
        except:
            return None

    def _get_amd_stats(self):
        if HAS_PYADL and self._adl_device:
            try:
                usage = self._adl_device.getCurrentUsage()
                try: temp = self._adl_device.getCurrentTemperature()
                except: temp = 0
                try: fan = self._adl_device.getCurrentFanSpeed()
                except: fan = 0
                
                generic = self._get_generic_stats()
                
                return {
                    "name": self.gpu_name,
                    "gpu_usage": usage,
                    "vram_total": self.vram_total or generic['vram_total'],
                    "vram_used": generic['vram_used'],
                    "vram_percent": generic['vram_percent'],
                    "temp": temp,
                    "power_draw": 0,
                    "fan_speed": fan,
                    "core_clock": 0,
                    "memory_clock": 0
                }
            except:
                pass
        
        return self._get_generic_stats()

    def _get_generic_stats(self):
        try:
            usage_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Engine(*3D*)\\\\Utilization Percentage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            usage = float(subprocess.check_output(usage_cmd, shell=True).decode().strip() or 0)
            
            vram_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Adapter Memory(*)\\\\Dedicated Usage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            vram_used_bytes = float(subprocess.check_output(vram_cmd, shell=True).decode().strip() or 0)
            vram_used = vram_used_bytes / 1024**2 # MB
            
            return {
                "name": self.gpu_name,
                "gpu_usage": int(usage),
                "vram_total": self.vram_total,
                "vram_used": vram_used,
                "vram_percent": (vram_used / self.vram_total) * 100 if self.vram_total > 0 else 0,
                "temp": 0,
                "power_draw": 0,
                "fan_speed": 0,
                "core_clock": 0,
                "memory_clock": 0
            }
        except:
            return None

    def cleanup(self):
        try:
            pynvml.nvmlShutdown()
        except:
            pass
