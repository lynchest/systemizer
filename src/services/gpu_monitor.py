import json
import logging
import subprocess
from typing import Optional, Dict, Any

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

try:
    from pyadl import ADLManager
    HAS_PYADL = True
except ImportError:
    HAS_PYADL = False

from src.exceptions import NvidiaLibraryError, AmdLibraryError, GpuMonitorError

# Set up logging for this module
logger = logging.getLogger(__name__)


class GPUMonitor:
    _instance: Optional['GPUMonitor'] = None
    _initialized: bool = False

    def __new__(cls) -> 'GPUMonitor':
        if cls._instance is None:
            cls._instance = super(GPUMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._gpu_available: bool = False
        self.vendor: str = "Unknown"
        self.gpu_name: str = "Detecting..."
        self.vram_total: int = 0  # In MB
        self._handle: Optional[Any] = None  # NVML device handle
        self._adl_device: Optional[Any] = None  # ADL device handle

        try:
            self.vendor = self._detect_vendor()
            logger.info(f"Detected GPU vendor: {self.vendor}")

            if self.vendor == "NVIDIA":
                self._init_nvidia()
            elif self.vendor == "AMD":
                self._init_amd()
            else:
                self._init_generic()

        except GpuMonitorError as e:
            logger.warning(f"Failed to initialize primary GPU monitor: {e}. Falling back to generic.")
            try:
                self._init_generic()
            except GpuMonitorError as generic_e:
                logger.error(f"Generic GPU monitor fallback also failed: {generic_e}")
                self.gpu_name = "No GPU Detected"
                self._gpu_available = False

        self.gpu_name = self._sanitize_name(self.gpu_name)
        self._initialized = True

    def is_gpu_available(self) -> bool:
        """Returns True if a GPU was successfully detected and initialized."""
        return self._gpu_available

    def _sanitize_name(self, name: str) -> str:
        """Cleans up GPU name by removing trademark symbols and extra whitespace."""
        if not name or not isinstance(name, str):
            return "Unknown GPU"

        replacements = {
            "™": "", "(TM)": "", "®": "", "(R)": "", "©": "", "(C)": "",
            "Corporation": "", "Graphics": "", "Series": ""
        }
        for old, new in replacements.items():
            name = name.replace(old, new)

        name = name.replace("NVIDIA", "Nvidia")
        return " ".join(name.split())

    def _detect_vendor(self) -> str:
        """Detects GPU vendor using PowerShell."""
        try:
            cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController | Select-Object Caption | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).decode('utf-8', errors='ignore').strip()
            if not output:
                raise GpuMonitorError("PowerShell command returned no output for Win32_VideoController.")

            data = json.loads(output)
            name = str(data[0].get("Caption", "") if isinstance(data, list) else data.get("Caption", "")).upper()

            if "NVIDIA" in name: return "NVIDIA"
            if "AMD" in name or "RADEON" in name: return "AMD"
            if "INTEL" in name: return "Intel"
            return "Generic"
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError, KeyError) as e:
            raise GpuMonitorError(f"Failed to detect GPU vendor via PowerShell: {e}") from e

    def _init_nvidia(self):
        """Initializes NVIDIA monitoring using NVML."""
        if not HAS_PYNVML:
            raise NvidiaLibraryError("pynvml library is not installed.")
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count == 0:
                raise NvidiaLibraryError("No NVIDIA devices found by NVML.")

            self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name_bytes = pynvml.nvmlDeviceGetName(self._handle)
            self.gpu_name = name_bytes.decode('utf-8')
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            self.vram_total = mem_info.total / (1024 ** 2)  # Convert bytes to MB
            self._gpu_available = True
            logger.info(f"Initialized NVIDIA GPU: {self.gpu_name}")
        except pynvml.NVMLError as e:
            raise NvidiaLibraryError(f"NVML error during initialization: {e}") from e

    def _init_amd(self):
        """Initializes AMD monitoring using pyadl."""
        if not HAS_PYADL:
            raise AmdLibraryError("pyadl library is not installed.")
        try:
            adl_devices = ADLManager.getInstance().getDevices()
            if not adl_devices:
                raise AmdLibraryError("No AMD devices found by pyadl.")

            self._adl_device = adl_devices[0]
            self.gpu_name = self._adl_device.adapterName.decode('utf-8')
            # ADL doesn't provide total VRAM, so we fall back to generic for that.
            self._init_generic(update_name=False)
            self._gpu_available = True
            logger.info(f"Initialized AMD GPU: {self.gpu_name}")
        except Exception as e:
            raise AmdLibraryError(f"ADL error during initialization: {e}") from e

    def _init_generic(self, update_name: bool = True):
        """Fallback to PowerShell for basic GPU info."""
        try:
            cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController | Select-Object -First 1 Caption, AdapterRAM | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).decode('utf-8', errors='ignore').strip()
            if not output:
                raise GpuMonitorError("Generic monitor PowerShell command returned no output.")

            data = json.loads(output)
            if update_name:
                self.gpu_name = data.get("Caption", "Generic GPU")

            ram_bytes = data.get("AdapterRAM", 0)
            if ram_bytes:
                self.vram_total = int(ram_bytes) / (1024 ** 2)
            self._gpu_available = True
            logger.info("Initialized generic GPU monitor.")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            raise GpuMonitorError(f"Failed to initialize generic monitor: {e}") from e

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Returns a dict of current GPU stats based on the initialized vendor."""
        if not self._gpu_available:
            return None

        try:
            if self.vendor == "NVIDIA" and self._handle:
                return self._get_nvidia_stats()
            elif self.vendor == "AMD" and self._adl_device:
                return self._get_amd_stats()
            else:
                return self._get_generic_stats()
        except Exception as e:
            logger.warning(f"Failed to get stats for {self.vendor} GPU: {e}")
            # Degrade gracefully: mark GPU as unavailable to stop further polling attempts
            self._gpu_available = False
            return None

    def _get_nvidia_stats(self) -> Dict[str, Any]:
        """Fetches stats from an initialized NVIDIA GPU."""
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            temp = pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU)
            
            power = pynvml.nvmlDeviceGetPowerUsage(self._handle) / 1000.0
            fan = pynvml.nvmlDeviceGetFanSpeed(self._handle)
            core_clock = pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_GRAPHICS)
            
            vram_used = mem_info.used / (1024 ** 2)
            vram_percent = (vram_used / self.vram_total * 100) if self.vram_total > 0 else 0
            
            return {
                "gpu_usage": util.gpu, "vram_total": self.vram_total, "vram_used": vram_used,
                "vram_percent": vram_percent, "temp": temp, "power_draw": power,
                "fan_speed": fan, "core_clock": core_clock
            }
        except pynvml.NVMLError as e:
            raise NvidiaLibraryError(f"Failed to get NVIDIA stats: {e}") from e

    def _get_amd_stats(self) -> Dict[str, Any]:
        """Fetches stats from an initialized AMD GPU."""
        try:
            usage = self._adl_device.getCurrentUsage()
            temp = self._adl_device.getCurrentTemperature()
            fan_obj = self._adl_device.getCurrentFanSpeed()
            fan = fan_obj.iSpeed if hasattr(fan_obj, 'iSpeed') else 0

            generic_stats = self._get_generic_stats_vram()
            
            return {
                "gpu_usage": usage, "vram_total": self.vram_total, "vram_used": generic_stats["vram_used"],
                "vram_percent": generic_stats["vram_percent"], "temp": temp, "power_draw": 0,
                "fan_speed": fan, "core_clock": 0
            }
        except Exception as e:
            raise AmdLibraryError(f"Failed to get AMD stats: {e}") from e

    def _get_generic_stats_vram(self) -> Dict[str, Any]:
        """A lightweight version of generic stats to get only VRAM."""
        try:
            vram_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Adapter Memory(*)\\\\Dedicated Usage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            vram_used_bytes = float(subprocess.check_output(vram_cmd, shell=True, stderr=subprocess.PIPE).decode().strip() or 0)
            vram_used = vram_used_bytes / (1024 ** 2)
            vram_percent = (vram_used / self.vram_total * 100) if self.vram_total > 0 else 0
            return {"vram_used": vram_used, "vram_percent": vram_percent}
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.warning(f"Could not fetch generic VRAM stats: {e}")
            return {"vram_used": 0, "vram_percent": 0}


    def _get_generic_stats(self) -> Dict[str, Any]:
        """Fetches generic stats using PowerShell counters."""
        try:
            usage_cmd = 'powershell -Command "(Get-Counter \'\\\\GPU Engine(*3D*)\\\\Utilization Percentage\' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Sum | Select-Object -ExpandProperty Sum"'
            usage = float(subprocess.check_output(usage_cmd, shell=True, stderr=subprocess.PIPE).decode().strip() or 0)
            
            vram_stats = self._get_generic_stats_vram()

            return {
                "gpu_usage": int(usage), "vram_total": self.vram_total, **vram_stats,
                "temp": 0, "power_draw": 0, "fan_speed": 0, "core_clock": 0
            }
        except (subprocess.CalledProcessError, ValueError) as e:
            raise GpuMonitorError(f"Failed to get generic stats: {e}") from e

    def cleanup(self) -> None:
        """Shuts down the NVML library if it was initialized."""
        if self.vendor == "NVIDIA" and HAS_PYNVML:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown successful.")
            except pynvml.NVMLError as e:
                logger.error(f"Error during NVML shutdown: {e}")
