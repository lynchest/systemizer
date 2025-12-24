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
            elif self.vendor == "Intel":
                self._init_intel()
            
            # 3. Fallback if vendor specific init failed
            if not self._gpu_available:
                self._init_generic()
            
            # 4. Cleanup name
            self.gpu_name = self._sanitize_name(self.gpu_name)
                
            self._initialized = True

    def _sanitize_name(self, name):
        """Clean up GPU name by removing trademark symbols and extra whitespace."""
        if not name:
            return "Unknown GPU"
            
        # Handle byte strings
        if isinstance(name, bytes):
            try:
                name = name.decode('utf-8', errors='ignore')
            except:
                name = str(name)

        # Remove common symbols that cause encoding issues in some UI environments
        replacements = {
            "™": "",
            "(TM)": "",
            "®": "",
            "(R)": "",
            "©": "",
            "(C)": "",
            "Corporation": "",
            "Graphics": "",
            "Series": "",
            "™": "",  # Double check common variants
            "": ""   # Replacement character
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
            
        # Also handle case-insensitive replacements for some
        name = name.replace("NVIDIA", "Nvidia")
        
        # Remove multiple spaces and strip
        name = " ".join(name.split())
        return name

    def _detect_vendor(self):
        """Detect GPU vendor using PowerShell."""
        try:
            # Use PowerShell with UTF-8 encoding for reliable character handling
            cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController | Select-Object Caption | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
            if not output: return "Unknown"
            
            data = json.loads(output)
            if isinstance(data, list):
                data = data[0] if data else {}
            
            name = str(data.get("Caption", "")).upper()
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

    def _init_intel(self):
        """Initialize Intel GPU monitoring using PowerShell."""
        try:
            cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController -Filter \\"DeviceName LIKE \'%Intel%\'\\" | Select-Object -First 1 Caption, AdapterRAM | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True, timeout=10).decode('utf-8', errors='ignore').strip()
            if output:
                data = json.loads(output)
                self.gpu_name = data.get("Caption", "Intel Graphics")
                ram_bytes = data.get("AdapterRAM", 0)
                if ram_bytes:
                    self.vram_total = int(ram_bytes) / 1024**2
                self._gpu_available = True
        except Exception as e:
            print(f"Failed to initialize Intel GPU: {e}")
            self._gpu_available = False

    def _init_generic(self):
        """Fallback to PowerShell for basic GPU info."""
        try:
            cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController | Select-Object -First 1 Caption, AdapterRAM | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
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
        elif self.vendor == "Intel":
            return self._get_intel_stats()
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
                try: 
                    fan_obj = self._adl_device.getCurrentFanSpeed()
                    # pyadl can return a FanSpeed object or sometimes just a value/dict
                    fan = getattr(fan_obj, 'iSpeed', fan_obj)
                    if not isinstance(fan, (int, float)):
                        fan = 0
                except: 
                    fan = 0
                
                generic = self._get_generic_stats()
                
                return {
                    "name": self.gpu_name,
                    "gpu_usage": usage,
                    "vram_total": self.vram_total or (generic['vram_total'] if generic else 0),
                    "vram_used": generic['vram_used'] if generic else 0,
                    "vram_percent": generic['vram_percent'] if generic else 0,
                    "temp": temp,
                    "power_draw": 0,
                    "fan_speed": fan,
                    "core_clock": 0,
                    "memory_clock": 0
                }
            except:
                pass
        
        return self._get_generic_stats()

    def _get_intel_stats(self):
        """Get Intel GPU statistics using Windows Performance Monitor and PowerShell."""
        try:
            # Intel GPU usage
            usage_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Engine(*Intel*)\\\\Utilization Percentage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            try:
                usage = float(subprocess.check_output(usage_cmd, shell=True, timeout=5).decode().strip() or 0)
            except:
                usage = 0
            
            # Try to get temperature from WMI
            temp = 0
            try:
                temp_cmd = 'powershell -Command "Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1 | Select-Object -ExpandProperty CurrentTemperature | ForEach-Object {($_ - 2732) / 10}"'
                temp_output = subprocess.check_output(temp_cmd, shell=True, timeout=5).decode().strip()
                if temp_output:
                    temp = float(temp_output)
            except:
                temp = 0
            
            # Intel shared GPU memory (Intel VRAM is typically shared system RAM)
            vram_used = 0
            vram_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Adapter Memory(*)\\\\Dedicated Usage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            try:
                vram_used_bytes = float(subprocess.check_output(vram_cmd, shell=True, timeout=5).decode().strip() or 0)
                vram_used = vram_used_bytes / 1024**2  # MB
            except:
                vram_used = 0
            
            return {
                "name": self.gpu_name,
                "gpu_usage": int(usage),
                "vram_total": self.vram_total,
                "vram_used": vram_used,
                "vram_percent": (vram_used / self.vram_total) * 100 if self.vram_total > 0 else 0,
                "temp": int(temp),
                "power_draw": 0,
                "fan_speed": 0,
                "core_clock": 0,
                "memory_clock": 0
            }
        except Exception as e:
            print(f"Error getting Intel GPU stats: {e}")
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
