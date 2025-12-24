import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QPushButton

# QApplication manuel olarak oluşturulmaz veya içe aktarılmaz
from src.settings import get_settings

@pytest.fixture
def app(qtbot):
    """Ana pencere için bir test fikstürü oluştur."""
    # MainWindow'u fikstürün içinde içe aktar
    from src.ui.main_window import MainWindow

    # Ayarları taklit ederek testlerin gerçek ayar dosyalarını kirletmemesini sağla
    with patch('src.settings.Settings._load_settings'), \
         patch('src.settings.Settings._save_settings'):

        # Test için yeni bir ayar örneği al
        settings = get_settings()
        settings.settings = settings.DEFAULT_SETTINGS.copy()

        # Ana pencereyi oluştur
        window = MainWindow()
        qtbot.addWidget(window)
        yield window

def test_main_window_init(app):
    """Ana pencerenin doğru bir şekilde başlatıldığını test et."""
    assert app.windowTitle() == "SYSTEMIZER"
    assert app.centralWidget() is not None

    # Ayarlar düğmesinin mevcut olduğunu doğrula
    settings_button = app.findChild(QPushButton, "Settings")
    assert settings_button is not None

@patch('src.ui.main_window.SettingsDialog')
def test_open_settings_dialog(mock_settings_dialog, app, qtbot):
    """Ayarlar düğmesine tıklandığında ayarlar iletişim kutusunun açıldığını test et."""
    # Ayarlar düğmesini bul ve tıkla
    settings_button = app.findChild(QPushButton, "Settings")
    qtbot.mouseClick(settings_button, pytest.qt.Qt.LeftButton)

    # SettingsDialog'un bir örneğinin oluşturulduğunu ve yürütüldüğünü doğrula
    mock_settings_dialog.assert_called_once()
    instance = mock_settings_dialog.return_value
    instance.exec.assert_called_once()

def test_apply_theme(app):
    """Tema ayarlarının pencereye doğru bir şekilde uygulandığını test et."""
    settings = get_settings()

    # Temayı özel bir renge ayarla
    custom_color = "#1a2a3a" # Koyu Mavi
    settings.set_setting('theme.background_main', custom_color)

    # apply_theme'i manuel olarak çağır
    app.apply_theme()

    # Stil sayfasının doğru bir şekilde ayarlandığını doğrula
    stylesheet = app.styleSheet().replace(" ", "").replace("\n", "")
    assert f"background-color:{custom_color};" in stylesheet

@patch('src.ui.main_window.SettingsDialog')
def test_settings_changed_signal(mock_settings_dialog, app, qtbot):
    """Ayarlar iletişim kutusu sinyal verdiğinde on_settings_changed'in çağrıldığını test et."""
    # on_settings_changed metodunu doğrudan app örneği üzerinde taklit et
    with patch.object(app, 'on_settings_changed') as mock_on_settings_changed:
        dialog_instance = mock_settings_dialog.return_value

        # Ayarlar düğmesine tıkla
        settings_button = app.findChild(QPushButton, "Settings")
        qtbot.mouseClick(settings_button, pytest.qt.Qt.LeftButton)

        # Sinyalin bağlandığını doğrula
        dialog_instance.settings_changed.connect.assert_called_with(app.on_settings_changed)

        # Sinyali manuel olarak yay ve slotun çağrılıp çağrılmadığını kontrol et
        dialog_instance.settings_changed.emit()
        mock_on_settings_changed.assert_called_once()
