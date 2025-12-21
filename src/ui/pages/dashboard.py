from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Slot
from src.ui.widgets.cards import StatCard
from src.services.gpu_monitor import GPUMonitor
from src.services.system_monitor import SystemMonitor
from src.services.data_collector import DataCollectorThread

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        
        self.gpu_monitor = GPUMonitor()
        self.sys_monitor = SystemMonitor()

        self.init_ui()
        
        # Background data collection thread (replaces timer)
        self.data_thread = DataCollectorThread()
        self.data_thread.fast_update.connect(self.on_fast_update)
        self.data_thread.medium_update.connect(self.on_medium_update)
        self.data_thread.slow_update.connect(self.on_slow_update)
        self.data_thread.gpu_update.connect(self.on_gpu_update)
        self.data_thread.start()

    def create_section(self, title, color):
        section = QFrame()
        section.setObjectName("SectionFrame")
        section.setStyleSheet(f"""
            QFrame#SectionFrame {{
                background-color: rgba(30, 30, 46, 120);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
            }}
            QLabel#SectionTitle {{
                color: {color};
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 2px;
                padding: 10px 0px 5px 0px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("SectionTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        layout.addLayout(grid)
        
        return section, grid

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 25)
        main_layout.setSpacing(20)
        
        # Header
        gpu_name = self.gpu_monitor.gpu_name if hasattr(self.gpu_monitor, 'gpu_name') else "System"
        header = QLabel(f"SYSTEMIZER — {gpu_name}")
        header.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold; font-family: 'Segoe UI';")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Create Cards
        self.card_cpu = StatCard("CPU Usage", "#f38ba8")
        self.card_ram = StatCard("RAM Usage", "#fab387")
        self.card_gpu = StatCard("GPU Usage", "#a6e3a1")
        self.card_vram = StatCard("VRAM Usage", "#89b4fa")
        
        self.card_gpu_temp = StatCard("GPU Temp", "#eba0ac")
        self.card_gpu_power = StatCard("GPU Power", "#f9e2af")
        self.card_gpu_fan = StatCard("GPU Fan", "#94e2d5")
        self.card_gpu_clock = StatCard("GPU Clock", "#cba6f7")

        self.card_disk = StatCard("Disk Usage", "#f5c2e7")
        self.card_net_down = StatCard("Net Down", "#74c7ec")
        self.card_net_up = StatCard("Net Up", "#b4befe")
        self.card_processes = StatCard("Processes", "#f2cdcd")
        self.card_uptime = StatCard("Uptime", "#f5e0dc")
        self.card_cores = StatCard("CPU Cores", "#a6e3a1")
        self.card_ram_speed = StatCard("RAM Speed", "#f9e2af")

        # Top Horizontal Layout for main groups
        top_groups = QHBoxLayout()
        top_groups.setSpacing(15)
        main_layout.addLayout(top_groups)

        # 1. CPU Group
        cpu_section, cpu_grid = self.create_section("Processor", "#f38ba8")
        cpu_grid.addWidget(self.card_cpu, 0, 0)
        cpu_grid.addWidget(self.card_cores, 0, 1)
        cpu_grid.addWidget(self.card_ram, 1, 0)
        cpu_grid.addWidget(self.card_ram_speed, 1, 1)
        cpu_grid.addWidget(self.card_processes, 2, 0)
        cpu_grid.addWidget(self.card_uptime, 2, 1)
        top_groups.addWidget(cpu_section)

        # 2. GPU Group
        gpu_section, gpu_grid = self.create_section("Graphics", "#a6e3a1")
        gpu_grid.addWidget(self.card_gpu, 0, 0)
        gpu_grid.addWidget(self.card_vram, 0, 1)
        gpu_grid.addWidget(self.card_gpu_temp, 1, 0)
        gpu_grid.addWidget(self.card_gpu_power, 1, 1)
        gpu_grid.addWidget(self.card_gpu_fan, 2, 0)
        gpu_grid.addWidget(self.card_gpu_clock, 2, 1)
        top_groups.addWidget(gpu_section)

        # 3. Bottom Group (Network & Disk)
        io_section, io_grid = self.create_section("System & Network", "#89b4fa")
        io_grid.addWidget(self.card_disk, 0, 0)
        io_grid.addWidget(self.card_net_down, 0, 1)
        io_grid.addWidget(self.card_net_up, 0, 2)
        main_layout.addWidget(io_section)

        main_layout.addStretch()
        
        # Initialize static data
        cpu = self.sys_monitor.get_cpu_stats()
        self.card_cores.update_value(f"{len(cpu['per_core'])} Cores", 0)

    @Slot(dict)
    def on_fast_update(self, data):
        """Handle fast updates (CPU, RAM, Network) from background thread."""
        # CPU
        self.card_cpu.update_value(f"{data['cpu_usage']:.0f}%", int(data['cpu_usage']))
        
        # RAM
        ram_text = f"{data['ram_used']:.1f} / {data['ram_total']:.1f} GB"
        self.card_ram.update_value(f"{data['ram_percent']:.0f}%", int(data['ram_percent']), ram_text)
        self.card_ram_speed.update_value(data['ram_speed'], 0)
        
        # Network
        self.card_net_down.update_value(
            f"{data['net_down_speed']:.1f} MB/s", 
            min(100, int(data['net_down_speed'] * 10))
        )
        self.card_net_up.update_value(
            f"{data['net_up_speed']:.1f} MB/s", 
            min(100, int(data['net_up_speed'] * 10))
        )
    
    @Slot(dict)
    def on_medium_update(self, data):
        """Handle medium updates (Processes) from background thread."""
        proc_count = data['process_count']
        self.card_processes.update_value(f"{proc_count}", min(100, int(proc_count / 5)))
    
    @Slot(dict)
    def on_slow_update(self, data):
        """Handle slow updates (Disk, Uptime) from background thread."""
        # Disk
        self.card_disk.update_value(f"{data['disk_percent']:.0f}%", int(data['disk_percent']))
        
        # Uptime
        self.card_uptime.update_value(
            f"{data['uptime_hours']}h {data['uptime_minutes']}m", 
            0
        )
    
    @Slot(dict)
    def on_gpu_update(self, data):
        """Handle GPU updates from background thread."""
        if data['available']:
            self.card_gpu.update_value(f"{data['gpu_usage']}%", data['gpu_usage'])
            vram_text = f"{data['vram_used']} / {data['vram_total']} GB"
            self.card_vram.update_value(f"{data['vram_percent']:.0f}%", int(data['vram_percent']), vram_text)
            self.card_gpu_temp.update_value(f"{data['temp']}°C", data['temp'])
            self.card_gpu_power.update_value(
                f"{data['power_draw']} W", 
                int(data['power_draw'] / 300 * 100)  # Normalized to 300W
            )
            self.card_gpu_fan.update_value(f"{data['fan_speed']}%", data['fan_speed'])
            self.card_gpu_clock.update_value(
                f"{data['core_clock']} MHz", 
                int(data['core_clock'] / 2500 * 100)  # Normalized to 2500MHz
            )
        else:
            # GPU not available - set all to N/A
            for card in [self.card_gpu, self.card_vram, self.card_gpu_temp, 
                        self.card_gpu_power, self.card_gpu_fan, self.card_gpu_clock]:
                card.update_value("N/A", 0)
    
    def closeEvent(self, event):
        """Clean up background thread when closing."""
        if hasattr(self, 'data_thread'):
            self.data_thread.stop()
            self.data_thread.wait()
        event.accept()

