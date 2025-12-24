from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsDropShadowEffect, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PySide6.QtCore import QSize
import webbrowser

class StatCard(QFrame):
    def __init__(self, title, color="#89b4fa", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        # Set a clear fixed size to avoid grid compression
        self.setFixedSize(180, 90)
        
        self.title = title
        self.value = "0"
        self.subtitle = ""
        self.percent = 0
        self.progress_color = QColor(color)

        # Style override for the card
        self.setStyleSheet("""
            QFrame.Card {
                background-color: rgba(49, 50, 68, 150);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(6)
        
        # Title
        self.lbl_title = QLabel(self.title)
        self.lbl_title.setObjectName("CardTitle")
        self.lbl_title.setStyleSheet("font-size: 10px; color: #a6adc8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;")
        self.layout.addWidget(self.lbl_title)
        
        # Value
        self.lbl_value = QLabel(self.value)
        self.lbl_value.setObjectName("CardValue")
        self.lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet("font-size: 16px; color: #ffffff; font-weight: bold;")
        self.layout.addWidget(self.lbl_value)

        # Subtitle (Additional info like GB used)
        self.lbl_subtitle = QLabel(self.subtitle)
        self.lbl_subtitle.setObjectName("CardSubtitle")
        self.lbl_subtitle.setStyleSheet("font-size: 10px; color: #9399b2; font-weight: 400;")
        self.layout.addWidget(self.lbl_subtitle)
        
        self.layout.addStretch()

    def update_value(self, value_str, percent, subtitle_str=""):
        """Update card value with dirty checking to avoid unnecessary redraws."""
        # Only update if value, percent, or subtitle has changed (dirty checking)
        if self.value != value_str or self.percent != percent or self.subtitle != subtitle_str:
            self.value = value_str
            self.percent = percent
            self.subtitle = subtitle_str
            self.lbl_value.setText(self.value)
            self.lbl_subtitle.setText(self.subtitle)
            self.update()  # Only repaint if data changed

    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        
        # Ring Dimensions
        ring_size = 38
        x = width - ring_size - 12
        y = (height - ring_size) / 2
        rect = QRectF(x, y, ring_size, ring_size)

        # Background Ring (Track)
        pen_bg = QPen(QColor(69, 71, 90, 100))
        pen_bg.setWidth(4)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        # Foreground Ring (Progress)
        pen_fg = QPen(self.progress_color)
        pen_fg.setWidth(4)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        
        span_angle = int(-self.percent * 360 * 16 / 100)
        painter.drawArc(rect, 90 * 16, span_angle)

class GPUUpdateCard(QFrame):
    """Card for GPU driver update notifications."""
    
    check_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "UpdateCard")
        self.setMinimumHeight(95)
        
        self.gpu_vendor = "Unknown"
        self.has_update = False
        self.current_version = None
        self.latest_version = None
        
        # Style override for the card
        self.setStyleSheet("""
            QFrame.UpdateCard {
                background-color: rgba(49, 50, 68, 150);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)
        
        # Title
        self.lbl_title = QLabel("Driver Kontrol")
        self.lbl_title.setObjectName("CardTitle")
        self.lbl_title.setStyleSheet("font-size: 9px; color: #a6adc8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;")
        main_layout.addWidget(self.lbl_title)
        
        # Status label
        self.lbl_status = QLabel("Checking...")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #89b4fa; font-weight: 600;")
        main_layout.addWidget(self.lbl_status)
        
        # Version info
        self.lbl_version = QLabel("")
        self.lbl_version.setStyleSheet("font-size: 9px; color: #a6adc8;")
        self.lbl_version.setWordWrap(True)
        main_layout.addWidget(self.lbl_version)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 3, 0, 0)
        button_layout.setSpacing(6)
        button_layout.addStretch()
        
        self.btn_check = QPushButton("Update Kontrolü Yap")
        self.btn_check.setStyleSheet("""
            QPushButton {
                background-color: rgba(166, 227, 161, 220);
                color: #000;
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: 600;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(166, 227, 161, 255);
            }
            QPushButton:pressed {
                background-color: rgba(137, 180, 250, 200);
            }
            QPushButton:disabled {
                background-color: rgba(88, 91, 112, 100);
                color: #6c7086;
            }
        """)
        self.btn_check.setMinimumWidth(120)
        self.btn_check.setFixedHeight(28)
        self.btn_check.clicked.connect(self.on_check_clicked)
        button_layout.addWidget(self.btn_check)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def update_status(self, has_update: bool, vendor: str, current_version: str, latest_version: str):
        """Update the card with new status information."""
        self.has_update = has_update
        self.gpu_vendor = vendor
        self.current_version = current_version
        self.latest_version = latest_version
        
        if vendor == "Unknown" or current_version is None:
            self.lbl_status.setText("GPU Algılanamadı")
            self.lbl_status.setStyleSheet("font-size: 13px; color: #9399b2; font-weight: 600;")
            self.lbl_version.setText("")
            self.btn_check.setEnabled(False)
        elif has_update:
            self.lbl_status.setText("⬆ Güncelleme Mevcut!")
            self.lbl_status.setStyleSheet("font-size: 13px; color: #a6e3a1; font-weight: 600;")
            self.lbl_version.setText(f"{vendor} Sürücü: {current_version} → {latest_version}")
            self.lbl_version.setStyleSheet("font-size: 11px; color: #a6e3a1;")
            self.btn_check.setEnabled(True)
        else:
            self.lbl_status.setText("✓ Güncel")
            self.lbl_status.setStyleSheet("font-size: 13px; color: #b4befe; font-weight: 600;")
            self.lbl_version.setText(f"{vendor} Sürücü: {current_version}")
            self.lbl_version.setStyleSheet("font-size: 11px; color: #a6adc8;")
            self.btn_check.setEnabled(True)
    
    def on_check_clicked(self):
        """Handle check button click."""
        self.btn_check.setEnabled(False)
        self.lbl_status.setText("Kontrol Ediliyor...")
        self.lbl_status.setStyleSheet("font-size: 13px; color: #89b4fa; font-weight: 600;")
        self.check_clicked.emit()
    
    def set_checking(self):
        """Set card to checking state."""
        self.btn_check.setEnabled(False)
        self.lbl_status.setText("Kontrol Ediliyor...")
        self.lbl_status.setStyleSheet("font-size: 13px; color: #89b4fa; font-weight: 600;")