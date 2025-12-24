from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Slot, QTimer, QPropertyAnimation, QEasingCurve, Property, Signal
from PySide6.QtGui import QIcon
from src.ui.widgets.cards import StatCard, GPUUpdateCard
from src.services.gpu_monitor import GPUMonitor
from src.services.system_monitor import SystemMonitor
from src.services.data_collector import DataCollectorThread
from src.services.gpu_driver_updater import GPUDriverUpdater
from src.settings import get_settings
from typing import Dict, Tuple, Optional

class CollapsibleSection(QFrame):
    """Katlanabilir bölüm widget'ı - yeniden kullanılabilir"""
    
    section_toggled = Signal(str, bool)  # section_name, is_expanded
    
    def __init__(self, title: str, color: str, section_name: str = "", parent=None):
        super().__init__(parent)
        self.color = color
        self.section_name = section_name
        self.is_expanded = True
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        self.setObjectName("SectionFrame")
        self.setStyleSheet(f"""
            QFrame#SectionFrame {{
                background-color: rgba(30, 30, 46, 120);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
            }}
            QLabel#SectionTitle {{
                color: {self.color};
                font-size: 9px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 4, 15, 12)
        layout.setSpacing(0)
        self.setMinimumHeight(0)
        
        # Header
        self._create_header(title, layout)
        
        # Content container
        self.content = QWidget()
        self.content.setMinimumHeight(0)
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)
        layout.addWidget(self.content)
    
    def _create_header(self, title: str, parent_layout: QVBoxLayout):
        """Header bileşenini oluştur"""
        header = QWidget()
        header.setMaximumHeight(32)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 6)
        
        # Hizalama için boşluk
        header_layout.addWidget(self._create_spacer())
        header_layout.addStretch()
        
        # Başlık
        title_lbl = QLabel(title)
        title_lbl.setObjectName("SectionTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setMaximumHeight(20)
        header_layout.addWidget(title_lbl)
        
        header_layout.addStretch()
        
        # Toggle butonu
        self.toggle_btn = self._create_toggle_button()
        header_layout.addWidget(self.toggle_btn)
        
        parent_layout.addWidget(header)
    
    def _create_spacer(self) -> QWidget:
        """Hizalama için dummy spacer"""
        spacer = QWidget()
        spacer.setFixedSize(20, 20)
        return spacer
    
    def _create_toggle_button(self) -> QPushButton:
        """Toggle butonunu oluştur"""
        btn = QPushButton("▼")
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.color};
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }}
        """)
        btn.clicked.connect(self.toggle)
        return btn
    
    def toggle(self):
        """Bölümü aç/kapat"""
        window = self.window()
        if window:
            window.setUpdatesEnabled(False)
        
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content.setMaximumHeight(16777215)
            self.toggle_btn.setText("▼")
        else:
            self.content.setMaximumHeight(0)
            self.toggle_btn.setText("▶")
        
        # Bölüm durumu değiştiğinde sinyal gönder
        self.section_toggled.emit(self.section_name, self.is_expanded)
        
        # Layout'u zorla güncelle
        self.adjustSize()
        self.updateGeometry()
        
        if window:
            window.setUpdatesEnabled(True)
            # Parent widget'tan resize tetikle - daha uzun delay
            if hasattr(self.parent(), 'update_window_size'):
                QTimer.singleShot(10, self.parent().update_window_size)
    
    def add_widget(self, widget: QWidget, row: int, col: int):
        """Grid'e widget ekle"""
        self.grid.addWidget(widget, row, col)


class DashboardPage(QWidget):
    """Ana dashboard sayfası"""
    
    # Statistic key mappings
    STAT_KEYS = [
        'cpu', 'ram', 'gpu', 'vram', 'gpu_temp', 'gpu_power',
        'gpu_fan', 'gpu_clock', 'disk', 'net_down', 'net_up',
        'processes', 'uptime', 'cpu_cores', 'ram_speed'
    ]
    
    # GPU normalization constants
    GPU_POWER_MAX = 300  # Watt
    GPU_CLOCK_MAX = 2500  # MHz
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.gpu_monitor = GPUMonitor()
        self.sys_monitor = SystemMonitor()
        self.settings = get_settings()
        self.gpu_updater = GPUDriverUpdater()
        
        # Storage
        self.cards: Dict[str, StatCard] = {}
        self.sections: Dict[str, CollapsibleSection] = {}
        self.data_thread: Optional[DataCollectorThread] = None
        
        self._init_ui()
        self._start_monitoring()
        self._check_driver_updates()
    
    def _init_ui(self):
        """UI bileşenlerini başlat"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 20)
        main_layout.setSpacing(15)
        
        self._create_cards()
        self._create_sections(main_layout)
        self._initialize_static_data()
        self.refresh_visibility()
    
    def _create_cards(self):
        """Tüm stat kartlarını oluştur"""
        card_configs = [
            ('cpu', 'CPU Usage', '#f38ba8'),
            ('ram', 'RAM Usage', '#fab387'),
            ('gpu', 'GPU Usage', '#a6e3a1'),
            ('vram', 'VRAM Usage', '#89b4fa'),
            ('gpu_temp', 'GPU Temp', '#eba0ac'),
            ('gpu_power', 'GPU Power', '#f9e2af'),
            ('gpu_fan', 'GPU Fan', '#94e2d5'),
            ('gpu_clock', 'GPU Clock', '#cba6f7'),
            ('disk', 'Disk Usage', '#f5c2e7'),
            ('net_down', 'Net Down', '#74c7ec'),
            ('net_up', 'Net Up', '#b4befe'),
            ('processes', 'Processes', '#f2cdcd'),
            ('uptime', 'Uptime', '#f5e0dc'),
            ('cpu_cores', 'CPU Cores', '#a6e3a1'),
            ('ram_speed', 'RAM Speed', '#f9e2af'),
        ]
        
        for key, title, color in card_configs:
            self.cards[key] = StatCard(title, color)
    
    def _create_sections(self, main_layout: QVBoxLayout):
        """Tüm bölümleri oluştur ve kartları yerleştir"""
        # Üst satır - CPU ve GPU
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # CPU Section
        cpu_section = CollapsibleSection("Processor", "#f38ba8", "cpu", self)
        self.sections['cpu'] = cpu_section
        cpu_section.section_toggled.connect(self._on_section_toggled)
        cpu_section.add_widget(self.cards['cpu'], 0, 0)
        cpu_section.add_widget(self.cards['cpu_cores'], 0, 1)
        cpu_section.add_widget(self.cards['ram'], 1, 0)
        cpu_section.add_widget(self.cards['ram_speed'], 1, 1)
        cpu_section.add_widget(self.cards['processes'], 2, 0)
        cpu_section.add_widget(self.cards['uptime'], 2, 1)
        top_row.addWidget(cpu_section)
        
        # GPU Section
        gpu_section = CollapsibleSection("Graphics", "#a6e3a1", "gpu", self)
        self.sections['gpu'] = gpu_section
        gpu_section.section_toggled.connect(self._on_section_toggled)
        gpu_section.add_widget(self.cards['gpu'], 0, 0)
        gpu_section.add_widget(self.cards['vram'], 0, 1)
        gpu_section.add_widget(self.cards['gpu_temp'], 1, 0)
        gpu_section.add_widget(self.cards['gpu_power'], 1, 1)
        gpu_section.add_widget(self.cards['gpu_fan'], 2, 0)
        gpu_section.add_widget(self.cards['gpu_clock'], 2, 1)
        top_row.addWidget(gpu_section)
        
        main_layout.addLayout(top_row)
        
        # System & Network Section
        io_section = CollapsibleSection("System & Network", "#89b4fa", "system", self)
        self.sections['system'] = io_section
        io_section.section_toggled.connect(self._on_section_toggled)
        io_section.add_widget(self.cards['disk'], 0, 0)
        io_section.add_widget(self.cards['net_down'], 0, 1)
        io_section.add_widget(self.cards['net_up'], 0, 2)
        main_layout.addWidget(io_section)
        
        # Driver Section
        driver_section = CollapsibleSection("Driver", "#f9e2af", "driver", self)
        self.sections['driver'] = driver_section
        driver_section.section_toggled.connect(self._on_section_toggled)
        self.card_gpu_update = GPUUpdateCard()
        self.card_gpu_update.check_clicked.connect(self._on_gpu_update_check_clicked)
        driver_section.add_widget(self.card_gpu_update, 0, 0)
        main_layout.addWidget(driver_section)
    
    def _initialize_static_data(self):
        """Statik verileri başlat"""
        cpu = self.sys_monitor.get_cpu_stats()
        self.cards['cpu_cores'].update_value(f"{len(cpu['per_core'])} Cores", 100)
    
    def _start_monitoring(self):
        """Arka plan izleme thread'ini başlat"""
        self.data_thread = DataCollectorThread()
        self.data_thread.fast_update.connect(self._on_fast_update)
        self.data_thread.medium_update.connect(self._on_medium_update)
        self.data_thread.slow_update.connect(self._on_slow_update)
        self.data_thread.gpu_update.connect(self._on_gpu_update)
        self.data_thread.start()
    
    def _check_driver_updates(self):
        """GPU sürücü güncellemelerini kontrol et"""
        if self.settings.get_setting("gpu_updates.check_enabled", True):
            self.gpu_updater.check_for_updates_async(self._on_driver_update_check)
    
    @Slot(dict)
    def _on_fast_update(self, data: dict):
        """Hızlı güncellemeleri işle (CPU, RAM, Network)"""
        self._update_card_if_enabled('cpu', data, 'cpu_usage', 
                                     lambda v: (f"{v:.0f}%", int(v)))
        
        if 'ram_percent' in data and self.settings.is_statistic_enabled('ram'):
            ram_text = f"{data['ram_used']:.1f} / {data['ram_total']:.1f} GB"
            self.cards['ram'].update_value(
                f"{data['ram_percent']:.0f}%", 
                int(data['ram_percent']), 
                ram_text
            )
        
        self._update_card_if_enabled('ram_speed', data, 'ram_speed',
                                     lambda v: (v, 100))
        
        self._update_card_if_enabled('net_down', data, 'net_down_speed',
                                     lambda v: self._format_network_speed(v))
        
        self._update_card_if_enabled('net_up', data, 'net_up_speed',
                                     lambda v: self._format_network_speed(v))
    
    @Slot(dict)
    def _on_medium_update(self, data: dict):
        """Orta hız güncellemeleri işle (Processes)"""
        self._update_card_if_enabled('processes', data, 'process_count',
                                     lambda v: (f"{v}", min(100, int(v / 5))))
    
    @Slot(dict)
    def _on_slow_update(self, data: dict):
        """Yavaş güncellemeleri işle (Disk, Uptime)"""
        self._update_card_if_enabled('disk', data, 'disk_percent',
                                     lambda v: (f"{v:.0f}%", int(v)))
        
        if 'uptime_hours' in data and self.settings.is_statistic_enabled('uptime'):
            self.cards['uptime'].update_value(
                f"{data['uptime_hours']}h {data['uptime_minutes']}m",
                100
            )
    
    @Slot(dict)
    def _on_gpu_update(self, data: dict):
        """GPU güncellemelerini işle"""
        if not data.get('available'):
            self._set_gpu_unavailable()
            return
        
        gpu_updates = [
            ('gpu', 'gpu_usage', lambda v: (f"{v}%", v)),
            ('gpu_temp', 'temp', lambda v: (f"{v}°C", v)),
            ('gpu_fan', 'fan_speed', lambda v: (f"{v}%", v)),
            ('gpu_power', 'power_draw', 
             lambda v: (f"{v} W", int(v / self.GPU_POWER_MAX * 100))),
            ('gpu_clock', 'core_clock',
             lambda v: (f"{v} MHz", int(v / self.GPU_CLOCK_MAX * 100))),
        ]
        
        for card_key, data_key, formatter in gpu_updates:
            self._update_card_if_enabled(card_key, data, data_key, formatter)
        
        # VRAM özel durum
        if 'vram_percent' in data and self.settings.is_statistic_enabled('vram'):
            vram_text = f"{data['vram_used']} / {data['vram_total']} GB"
            self.cards['vram'].update_value(
                f"{data['vram_percent']:.0f}%",
                int(data['vram_percent']),
                vram_text
            )
    
    def _update_card_if_enabled(self, card_key: str, data: dict, 
                                data_key: str, formatter):
        """Kart etkinse güncelle"""
        if data_key in data and self.settings.is_statistic_enabled(card_key):
            value, progress = formatter(data[data_key])
            self.cards[card_key].update_value(value, progress)
    
    def _format_network_speed(self, speed_kb: float) -> Tuple[str, int]:
        """Network hızını uygun birimde göster (KB/s veya MB/s)"""
        if speed_kb < 1024:
            # Show as KB/s for small values
            return (f"{speed_kb:.1f} KB/s", min(100, int(speed_kb / 10)))
        else:
            # Show as MB/s for larger values
            speed_mb = speed_kb / 1024
            # Progress bar: assume 100MB/s is 100%
            progress = min(100, int(speed_mb * 10))
            return (f"{speed_mb:.1f} MB/s", progress)
    
    def _set_gpu_unavailable(self):
        """GPU kullanılamadığında tüm GPU kartlarını N/A yap"""
        gpu_cards = ['gpu', 'vram', 'gpu_temp', 'gpu_power', 'gpu_fan', 'gpu_clock']
        for card_key in gpu_cards:
            self.cards[card_key].update_value("N/A", 0)
    
    @Slot(bool, object)
    def _on_driver_update_check(self, update_available: bool, latest_version):
        """Sürücü güncelleme kontrolü tamamlandığında"""
        update_info = self.gpu_updater.get_update_info()
        self.card_gpu_update.update_status(
            has_update=update_available,
            vendor=update_info['vendor'],
            current_version=update_info['current_version'] or 'Unknown',
            latest_version=latest_version or 'Unknown'
        )
    
    @Slot()
    def _on_gpu_update_check_clicked(self):
        """Manuel GPU güncelleme kontrolü"""
        self.card_gpu_update.set_checking()
        self.gpu_updater.check_for_updates_async(self._on_driver_update_check)
    
    def update_window_size(self):
        """Pencere boyutunu içeriğe göre ayarla"""
        window = self.window()
        if not window:
            return
        
        # Tüm section'ları kontrol et - hepsi kapalıysa minimum yükseklik
        any_expanded = any(
            section.is_expanded 
            for section in self.sections.values() 
            if isinstance(section, CollapsibleSection)
        )
        
        window.setUpdatesEnabled(False)
        
        # Layout'u güncelle
        self.layout().activate()
        self.adjustSize()
        self.updateGeometry()
        
        # Yeni boyutu hesapla
        size_hint = self.sizeHint()
        new_width = max(900, window.width())
        
        # Eğer hiçbir section açık değilse, minimum yükseklik
        if not any_expanded:
            # Header yükseklikleri + margin'lar
            min_height = 150  # Tüm header'lar + padding
            new_height = min_height
        else:
            new_height = size_hint.height()
        
        # Resize yap
        window.resize(new_width, new_height)
        
        # Widget'ı da resize et
        window.setUpdatesEnabled(True)
        window.update()
        
        # Bir kere daha güncelleme (Qt quirk için)
        QTimer.singleShot(20, lambda: self._final_resize(window, new_width, new_height))
    
    def _final_resize(self, window, width: int, height: int):
        """Final resize - Qt'nin layout hesaplamalarının bitmesini bekle"""
        if window:
            window.resize(width, height)
            window.updateGeometry()
    
    @Slot(str, bool)
    def _on_section_toggled(self, section_name: str, is_expanded: bool):
        """Bölüm açılıp kapatıldığında veri toplamayı kontrol et"""
        if not self.data_thread:
            return
        
        # Bölüm adlarına göre statistic key'lerini eşleştir
        section_to_stats = {
            'cpu': ['cpu', 'cpu_cores', 'ram', 'ram_speed', 'processes', 'uptime'],
            'gpu': ['gpu', 'vram', 'gpu_temp', 'gpu_power', 'gpu_fan', 'gpu_clock'],
            'system': ['disk', 'net_down', 'net_up'],
            'driver': []  # Driver bölümü veri toplama gerektirmez
        }
        
        # İlgili statistic'leri etkinleştir/devre dışı bırak
        stats_for_section = section_to_stats.get(section_name, [])
        for stat_key in stats_for_section:
            # Bölüm açıksa ve ayarlarda etkinse, veri toplama etkin
            # Bölüm kapalıysa, veri toplama devre dışı
            should_enable = is_expanded and self.settings.is_statistic_enabled(stat_key)
            self.data_thread.set_statistic_enabled(stat_key, should_enable)
        
        # Veri ihtiyaç varsa yenile
        if is_expanded:
            self.data_thread.force_refresh_all()
    
    def refresh_visibility(self):
        """Ayarlara göre kart görünürlüğünü yenile"""
        for stat_key in self.STAT_KEYS:
            if stat_key in self.cards:
                is_enabled = self.settings.is_statistic_enabled(stat_key)
                self.cards[stat_key].setVisible(is_enabled)
                
                if self.data_thread:
                    # Eğer bölüm açıksa statistic'i etkinleştir
                    self.data_thread.set_statistic_enabled(stat_key, is_enabled)
        
        if self.data_thread:
            self.data_thread.force_refresh_all()
    
    def closeEvent(self, event):
        """Pencere kapatılırken temizlik yap"""
        if self.data_thread:
            self.data_thread.stop()
            self.data_thread.wait()
        event.accept()