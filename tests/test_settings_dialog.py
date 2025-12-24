import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QCheckBox, QPushButton
from PySide6.QtCore import Signal

# QApplication manuel olarak oluşturulmaz
from src.settings import get_settings

@pytest.fixture
def dialog(qtbot):
    """Ayarlar iletişim kutusu için bir test fikstürü oluştur."""
    # SettingsDialog'u fikstürün içinde içe aktar
    from src.ui.dialogs.settings_dialog import SettingsDialog

    with patch('src.settings.Settings._load_settings'), \
         patch('src.settings.Settings._save_settings'):

        settings = get_settings()
        settings.settings = settings.DEFAULT_SETTINGS.copy()

        # Test için iletişim kutusunu oluştur
        d = SettingsDialog()
        qtbot.addWidget(d)
        yield d

def test_settings_dialog_init(dialog):
    """Ayarlar iletişim kutusunun doğru bir şekilde başlatıldığını test et."""
    assert dialog.windowTitle() == "Settings"

    # Tüm istatistik onay kutularının oluşturulduğunu ve doğru durumu yansıttığını doğrula
    for key in get_settings().DEFAULT_SETTINGS['statistics']:
        assert key in dialog.checkboxes
        checkbox = dialog.checkboxes[key]
        assert isinstance(checkbox, QCheckBox)
        assert checkbox.isChecked() == get_settings().is_statistic_enabled(key)

def test_checkbox_changes_settings(dialog, qtbot):
    """Bir onay kutusunun durumunu değiştirmenin ve 'Uygula'ya tıklamanın ayarları güncellediğini test et."""
    # CPU onay kutusunun işaretini kaldır
    cpu_checkbox = dialog.checkboxes['cpu']
    qtbot.mouseClick(cpu_checkbox, pytest.qt.Qt.LeftButton, delay=1)
    assert not cpu_checkbox.isChecked()

    # 'Uygula' düğmesini bul ve tıkla
    apply_button = dialog.findChild(QPushButton, "Apply")
    qtbot.mouseClick(apply_button, pytest.qt.Qt.LeftButton)

    # Ayarın güncellendiğini doğrula
    assert not get_settings().is_statistic_enabled('cpu')

def test_apply_button_emits_signals(dialog, qtbot):
    """'Uygula' düğmesine tıklandığında sinyallerin doğru şekilde yayıldığını test et."""
    with qtbot.waitSignals([dialog.settings_changed, dialog.theme_changed]) as blocker:
        apply_button = dialog.findChild(QPushButton, "Apply")
        qtbot.mouseClick(apply_button, pytest.qt.Qt.LeftButton)

    # Her sinyalin bir kez yayıldığını doğrula
    assert blocker.count == 2

def test_select_color_updates_theme(dialog, qtbot):
    """Bir renk düğmesine tıklamanın tema ayarlarını güncellediğini test et."""
    # Test için koyu kırmızı rengi seç
    dark_red_hex = "#3a1a1a"
    dark_red_button = dialog.color_buttons[dark_red_hex]

    # Düğmeye tıkla
    qtbot.mouseClick(dark_red_button, pytest.qt.Qt.LeftButton)

    # Geçici tema renginin güncellendiğini doğrula
    assert dialog.theme_colors['background_main'] == dark_red_hex

    # 'Uygula'ya tıkla
    apply_button = dialog.findChild(QPushButton, "Apply")
    qtbot.mouseClick(apply_button, pytest.qt.Qt.LeftButton)

    # Kalıcı ayarların güncellendiğini doğrula
    assert get_settings().get_theme_color('background_main') == dark_red_hex

def test_close_button(dialog, qtbot):
    """'Kapat' düğmesinin iletişim kutusunu kapattığını test et."""
    # close metodunun çağrıldığını doğrula
    with patch.object(dialog, 'close') as mock_close:
        close_button = dialog.findChild(QPushButton, "Close")
        qtbot.mouseClick(close_button, pytest.qt.Qt.LeftButton)
        mock_close.assert_called_once()
