from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

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
