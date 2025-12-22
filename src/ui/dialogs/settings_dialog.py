from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QCheckBox, QPushButton, QGroupBox, QGridLayout, QScrollArea,
                               QColorDialog, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from src.settings import get_settings


class SettingsDialog(QDialog):
    """Settings dialog for managing statistics visibility, collection, and theme colors."""
    
    # Signal emitted when settings change
    settings_changed = Signal()
    # Signal emitted when theme changes
    theme_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 650, 800)
        self.settings = get_settings()
        self.checkboxes = {}
        self.color_buttons = {}
        self.theme_colors = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Get current background color from settings
        bg_color = self.settings.get_theme_color("background_main")
        
        # Calculate a slightly lighter shade for borders/secondary elements
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        bg_alt = '#{:02x}{:02x}{:02x}'.format(
            min(int(bg_rgb[0] * 1.2), 255),
            min(int(bg_rgb[1] * 1.2), 255),
            min(int(bg_rgb[2] * 1.2), 255)
        )
        
        # Title
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #cdd6f4;")
        layout.addWidget(title)
        
        # Scroll area for all settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background-color: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        
        scroll_widget = self.create_settings_groups()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
            QPushButton:pressed {
                background-color: #89dceb;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #585b70;
                color: #cdd6f4;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6c7086;
            }
            QPushButton:pressed {
                background-color: #45475a;
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Apply theme to dialog - use background color from settings
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
            QGroupBox {{
                color: #cdd6f4;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: {bg_alt};

            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
            QCheckBox {{
                color: #cdd6f4;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background-color: #a6e3a1;
                border: 1px solid #a6e3a1;
                border-radius: 4px;
            }}
            QLabel {{
                color: #cdd6f4;
            }}
        """)
    
    def create_settings_groups(self):
        """Create all settings groups including statistics and theme."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Theme Colors Group
        main_layout.addWidget(self.create_theme_group())
        
        # Statistics Groups
        main_layout.addWidget(self.create_statistics_groups())
        
        main_layout.addStretch()
        
        container = QWidget()
        container.setLayout(main_layout)
        return container
    
    def create_theme_group(self):
        """Create the theme colors customization group."""
        theme_group = QGroupBox("Background Color")
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(10)
        
        # Load current theme background color
        self.theme_colors = self.settings.get_all_theme_colors()
        current_bg = self.theme_colors.get("background_main", "#1e1e2e")
        
        # Label
        label = QLabel("Choose Background Color:")
        label.setStyleSheet("color: #cdd6f4; font-weight: bold;")
        theme_layout.addWidget(label)
        
        # Create buttons for each color in the palette
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        for color_name, hex_color in self.settings.BACKGROUND_COLORS.items():
            btn = QPushButton()
            btn.setStyleSheet(self.get_color_button_style(hex_color, color_name))
            btn.setFixedSize(60, 60)
            btn.setToolTip(color_name)
            
            # Highlight current selection
            if hex_color == current_bg:
                btn.setStyleSheet(self.get_selected_color_button_style(hex_color, color_name))
            
            # Store reference and connect
            self.color_buttons[hex_color] = btn
            btn.clicked.connect(lambda checked=False, color=hex_color, name=color_name: self.select_color(color, name))
            
            button_layout.addWidget(btn)
        
        button_layout.addStretch()
        theme_layout.addLayout(button_layout)
        
        theme_group.setLayout(theme_layout)
        return theme_group
    
    def get_color_button_style(self, hex_color, color_name=""):
        """Generate stylesheet for a color button."""
        return f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                border: 2px solid rgba(255, 255, 255, 0.5);
            }}
        """
    
    def get_selected_color_button_style(self, hex_color, color_name=""):
        """Generate stylesheet for a selected color button."""
        return f"""
            QPushButton {{
                background-color: {hex_color};
                border: 3px solid #a6e3a1;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                border: 3px solid #a6e3a1;
            }}
        """
    
    def select_color(self, hex_color, color_name):
        """Select a color from the palette."""
        # Update the theme color
        self.theme_colors["background_main"] = hex_color
        
        # Update all buttons - reset style and highlight selected
        for btn_color, btn in self.color_buttons.items():
            if btn_color == hex_color:
                btn.setStyleSheet(self.get_selected_color_button_style(hex_color, color_name))
            else:
                btn.setStyleSheet(self.get_color_button_style(btn_color, ""))
    
    def pick_color(self, color_key):
        """Open color picker for the specified color key."""
        current_color = QColor(self.theme_colors.get(color_key, "#ffffff"))
        color = QColorDialog.getColor(current_color, self, f"Choose {color_key}")
        
        if color.isValid():
            hex_color = color.name()
            self.theme_colors[color_key] = hex_color
            
            # Update button style
            button = self.color_buttons[color_key]
            button.setStyleSheet(self.get_color_button_style(hex_color))
    
    
    def create_statistics_groups(self):
        """Create grouped checkboxes for statistics."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Processor Group
        processor_group = QGroupBox("Processor")
        processor_layout = QGridLayout()
        processor_layout.setSpacing(10)
        
        stats_proc = [
            ("cpu", "CPU Usage"),
            ("cpu_cores", "CPU Cores"),
            ("ram", "RAM Usage"),
            ("ram_speed", "RAM Speed"),
            ("processes", "Processes"),
            ("uptime", "Uptime"),
        ]
        
        for i, (key, label) in enumerate(stats_proc):
            cb = QCheckBox(label)
            cb.setChecked(self.settings.is_statistic_enabled(key))
            self.checkboxes[key] = cb
            processor_layout.addWidget(cb, i // 2, i % 2)
        
        processor_group.setLayout(processor_layout)
        main_layout.addWidget(processor_group)
        
        # Graphics Group
        graphics_group = QGroupBox("Graphics (GPU)")
        graphics_layout = QGridLayout()
        graphics_layout.setSpacing(10)
        
        stats_gpu = [
            ("gpu", "GPU Usage"),
            ("vram", "VRAM Usage"),
            ("gpu_temp", "GPU Temperature"),
            ("gpu_power", "GPU Power"),
            ("gpu_fan", "GPU Fan Speed"),
            ("gpu_clock", "GPU Clock"),
        ]
        
        for i, (key, label) in enumerate(stats_gpu):
            cb = QCheckBox(label)
            cb.setChecked(self.settings.is_statistic_enabled(key))
            self.checkboxes[key] = cb
            graphics_layout.addWidget(cb, i // 2, i % 2)
        
        graphics_group.setLayout(graphics_layout)
        main_layout.addWidget(graphics_group)
        
        # System & Network Group
        system_group = QGroupBox("System & Network")
        system_layout = QGridLayout()
        system_layout.setSpacing(10)
        
        stats_sys = [
            ("disk", "Disk Usage"),
            ("net_down", "Network Download"),
            ("net_up", "Network Upload"),
        ]
        
        for i, (key, label) in enumerate(stats_sys):
            cb = QCheckBox(label)
            cb.setChecked(self.settings.is_statistic_enabled(key))
            self.checkboxes[key] = cb
            system_layout.addWidget(cb, i, 0)
        
        system_group.setLayout(system_layout)
        main_layout.addWidget(system_group)
        
        container = QWidget()
        container.setLayout(main_layout)
        return container
    
    def apply_settings(self):
        """Save all settings and emit signals."""
        # Save statistics settings
        for stat_key, checkbox in self.checkboxes.items():
            self.settings.set_statistic(stat_key, checkbox.isChecked())
        
        # Save theme colors
        for color_key, hex_color in self.theme_colors.items():
            self.settings.set_theme_color(color_key, hex_color)
        
        # Emit signals
        self.settings_changed.emit()
        self.theme_changed.emit()
        self.close()
