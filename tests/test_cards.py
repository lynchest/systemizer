import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# QApplication manuel olarak oluşturulmaz

@pytest.fixture
def stat_card(qtbot):
    """StatCard için bir test fikstürü oluştur."""
    # StatCard'ı fikstürün içinde içe aktar
    from src.ui.widgets.cards import StatCard

    card = StatCard("CPU Test", color="#ff0000")
    qtbot.addWidget(card)
    yield card

def test_stat_card_init(stat_card):
    """StatCard'ın doğru bir şekilde başlatıldığını test et."""
    assert stat_card.title == "CPU Test"
    assert stat_card.lbl_title.text() == "CPU Test"
    assert stat_card.lbl_value.text() == "0"
    assert stat_card.progress_color == QColor("#ff0000")

def test_stat_card_update_value(stat_card):
    """StatCard'ın update_value ile doğru şekilde güncellendiğini test et."""
    stat_card.update_value("75%", 75, "3.2 GHz")

    assert stat_card.value == "75%"
    assert stat_card.percent == 75
    assert stat_card.subtitle == "3.2 GHz"
    assert stat_card.lbl_value.text() == "75%"
    assert stat_card.lbl_subtitle.text() == "3.2 GHz"

def test_stat_card_dirty_checking(stat_card):
    """update_value'nun gereksiz yeniden çizmeleri önlemek için kirli kontrolü kullandığını test et."""
    with patch.object(stat_card, 'update') as mock_update:
        stat_card.update_value("50%", 50)
        mock_update.assert_called_once()

        stat_card.update_value("50%", 50)
        mock_update.assert_called_once()

        stat_card.update_value("60%", 60)
        assert mock_update.call_count == 2

@pytest.fixture
def gpu_update_card(qtbot):
    """GPUUpdateCard için bir test fikstürü oluştur."""
    # GPUUpdateCard'ı fikstürün içinde içe aktar
    from src.ui.widgets.cards import GPUUpdateCard

    card = GPUUpdateCard()
    qtbot.addWidget(card)
    yield card

def test_gpu_update_card_init(gpu_update_card):
    """GPUUpdateCard'ın 'Kontrol ediliyor...' durumunda başladığını test et."""
    assert gpu_update_card.lbl_status.text() == "Checking..."
    assert "Kontrol Ediliyor..." not in gpu_update_card.btn_check.text()

def test_gpu_update_card_status_update_available(gpu_update_card):
    """Bir güncelleme mevcut olduğunda GPUUpdateCard'ın durumunu doğru şekilde güncellediğini test et."""
    gpu_update_card.update_status(
        has_update=True,
        vendor="NVIDIA",
        current_version="512.15",
        latest_version="512.77"
    )
    assert "Güncelleme Mevcut!" in gpu_update_card.lbl_status.text()
    assert "512.15 → 512.77" in gpu_update_card.lbl_version.text()

def test_gpu_update_card_status_up_to_date(gpu_update_card):
    """Sürücü güncel olduğunda GPUUpdateCard'ın durumunu doğru şekilde güncellediğini test et."""
    gpu_update_card.update_status(
        has_update=False,
        vendor="AMD",
        current_version="22.5.1",
        latest_version="22.5.1"
    )
    assert "Güncel" in gpu_update_card.lbl_status.text()
    assert "22.5.1" in gpu_update_card.lbl_version.text()
    assert "→" not in gpu_update_card.lbl_version.text()

def test_gpu_update_card_check_button_click(gpu_update_card, qtbot):
    """'Kontrol Et' düğmesine tıklandığında check_clicked sinyalinin yayıldığını ve durumun güncellendiğini test et."""
    with qtbot.waitSignal(gpu_update_card.check_clicked):
        qtbot.mouseClick(gpu_update_card.btn_check, Qt.LeftButton)

    assert not gpu_update_card.btn_check.isEnabled()
    assert "Kontrol Ediliyor..." in gpu_update_card.lbl_status.text()
