import pynvml

class GPUMonitor:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPUMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(0) if self.device_count > 0 else None
                name = pynvml.nvmlDeviceGetName(self._handle)
                if isinstance(name, bytes):
                    self.gpu_name = name.decode('utf-8')
                else:
                    self.gpu_name = name
                
                # Fetch total memory once
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
                self.vram_total = mem_info.total / 1024**2 # MB
                
                self._initialized = True
                self._gpu_available = True  # GPU is available
            except pynvml.NVMLError as e:
                print(f"NVML Init Failed: {e}")
                self._handle = None
                self.device_count = 0
                self.gpu_name = "NVIDIA Driver Not Found"
                self.vram_total = 1 # Avoid division by zero
                self._initialized = False
                self._gpu_available = False  # GPU not available

    def get_stats(self):
        """Returns a dict of current GPU stats."""
        # Lazy loading optimization: if GPU not available, return immediately
        if not self._gpu_available or not self._handle:
            return None

        try:
            # Usage
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            gpu_usage = util.gpu
            
            # Memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            vram_used = mem_info.used / 1024**2   # MB
            vram_percent = (vram_used / self.vram_total) * 100

            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU)

            # Power
            try:
                power_draw = pynvml.nvmlDeviceGetPowerUsage(self._handle) / 1000.0 # W
            except pynvml.NVMLError:
                power_draw = 0.0

            # Fan
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(self._handle)
            except pynvml.NVMLError:
                fan_speed = 0

            # Clocks
            core_clock = pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_GRAPHICS)
            mem_clock = pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_MEM)

            return {
                "name": self.gpu_name,
                "gpu_usage": gpu_usage,
                "vram_total": self.vram_total,
                "vram_used": vram_used,
                "vram_percent": vram_percent,
                "temp": temp,
                "power_draw": power_draw,
                "fan_speed": fan_speed,
                "core_clock": core_clock,
                "memory_clock": mem_clock
            }
        except pynvml.NVMLError:
            return None

    def cleanup(self):
        try:
            pynvml.nvmlShutdown()
        except:
            pass
