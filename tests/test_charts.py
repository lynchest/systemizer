import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtGui import QColor, QPainter

# QApplication manuel olarak oluşturulmaz

@pytest.fixture
def chart(qtbot):
    """LineChart için bir test fikstürü oluştur."""
    # LineChart'ı fikstürün içinde içe aktar
    from src.ui.widgets.charts import LineChart

    chart_widget = LineChart(color="#ff5555", max_points=10)
    qtbot.addWidget(chart_widget)
    yield chart_widget

def test_line_chart_init(chart):
    """LineChart'ın doğru özelliklerle başlatıldığını test et."""
    assert chart.max_points == 10
    assert chart.line_color == QColor("#ff5555")
    assert not chart.data_points

def test_add_point(chart):
    """add_point fonksiyonunun veri noktalarını listeye doğru şekilde eklediğini test et."""
    with patch.object(chart, 'update') as mock_update:
        chart.add_point(50)
        assert chart.data_points == [50]
        mock_update.assert_called_once()

        chart.add_point(75)
        assert chart.data_points == [50, 75]
        assert mock_update.call_count == 2

def test_max_points_capping(chart):
    """Veri noktası listesinin max_points'i aşmadığını test et."""
    for i in range(10):
        chart.add_point(i * 10)

    assert len(chart.data_points) == 10
    assert chart.data_points[0] == 0

    chart.add_point(100)

    assert len(chart.data_points) == 10
    assert chart.data_points[0] == 10
    assert chart.data_points[-1] == 100

@patch('src.ui.widgets.charts.QPainter')
def test_paint_event(mock_painter_class, chart):
    """paintEvent'in doğru çizim komutlarını çağırdığını test et."""
    mock_painter_instance = mock_painter_class.return_value

    chart.add_point(25)
    chart.add_point(50)
    chart.add_point(75)

    chart.paintEvent(None)

    # Check that setRenderHint was called
    assert mock_painter_instance.setRenderHint.called

    # Check that drawPolyline was called
    assert mock_painter_instance.drawPolyline.called

    # Check that drawPolygon was called
    assert mock_painter_instance.drawPolygon.called

def test_paint_event_no_data(chart):
    """Veri olmadığında paintEvent'in çizim yapmadığını test et."""
    with patch('src.ui.widgets.charts.QPainter') as mock_painter_class:
        mock_painter_instance = mock_painter_class.return_value

        chart.paintEvent(None)

        mock_painter_instance.drawPolyline.assert_not_called()
        mock_painter_instance.drawPolygon.assert_not_called()
