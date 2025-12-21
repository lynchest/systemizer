from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient

class LineChart(QFrame):
    def __init__(self, color="#89b4fa", max_points=60):
        super().__init__()
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: #313244; border-radius: 12px;")
        
        self.data_points = []
        self.max_points = max_points
        self.line_color = QColor(color)

    def add_point(self, value):
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        if not self.data_points:
            return

        # Scales
        x_step = width / (self.max_points - 1) if self.max_points > 1 else width
        # Max value usually 100 for percentages, but let's dynamic or fixed 100
        max_val = 100
        
        # Create Path
        points = []
        for i, val in enumerate(self.data_points):
            x = i * x_step
            # Invert Y (0 is top)
            y = height - (val / max_val * height)
            points.append(QPointF(x, y))
            
        # Draw Line
        pen = QPen(self.line_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPolyline(points)

        # Fill Area (Gradient)
        if len(points) > 1:
            path_points = [QPointF(0, height)] + points + [QPointF(points[-1].x(), height)]
            
            grad = QLinearGradient(0, 0, 0, height)
            c = QColor(self.line_color)
            c.setAlpha(100)
            grad.setColorAt(0, c)
            c.setAlpha(0)
            grad.setColorAt(1, c)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(grad)
            painter.drawPolygon(path_points)
