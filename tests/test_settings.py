import pytest
from unittest.mock import patch
import json
import tempfile
import shutil
from pathlib import Path

# Settings modülünü içe aktar
from src import settings
from src.settings import Settings, get_settings

@pytest.fixture(autouse=True)
def isolated_settings():
    """Her test için geçici bir ayar dizini oluşturan ve temizleyen bir fikstür."""
    # Geçici dizin oluştur
    temp_dir = tempfile.mkdtemp()

    # Path.home()'u yama
    with patch('pathlib.Path.home', return_value=Path(temp_dir)):
        # Global singleton örneğini sıfırla
        settings._settings_instance = None
        yield Path(temp_dir)

    # Geçici dizini temizle
    shutil.rmtree(temp_dir)

def test_initialization_no_file(isolated_settings):
    """Ayar dosyası olmadığında varsayılan ayarların kullanıldığını ve dosyanın oluşturulduğunu test et."""
    s = Settings()
    assert s.get_setting('statistics.cpu') is True
    assert s.get_setting('theme.background_main') == '#0d0d0d'

    settings_file = isolated_settings / ".systemizer" / "settings.json"
    assert settings_file.exists()

def test_load_existing_settings(isolated_settings):
    """Mevcut bir ayar dosyasının doğru bir şekilde yüklendiğini test et."""
    settings_dir = isolated_settings / ".systemizer"
    settings_dir.mkdir()
    settings_file = settings_dir / "settings.json"

    custom_settings = {
        "statistics": {"cpu": False},
        "theme": {"background_main": "#1a1a1a"}
    }

    with open(settings_file, 'w') as f:
        json.dump(custom_settings, f)

    s = Settings()

    assert s.get_setting('statistics.cpu') is False
    assert s.get_setting('statistics.gpu') is True  # Varsayılan değer
    assert s.get_setting('theme.background_main') == '#1a1a1a'

def test_set_and_get_setting(isolated_settings):
    """Ayarların nokta notasyonu ile ayarlanıp alınabildiğini test et."""
    s = Settings()

    s.set_setting('statistics.gpu_temp', False)
    s.set_setting('theme.new_color', '#ff0000')

    assert s.get_setting('statistics.gpu_temp') is False
    assert s.get_setting('theme.new_color') == '#ff0000'

    settings_file = isolated_settings / ".systemizer" / "settings.json"
    with open(settings_file, 'r') as f:
        saved_settings = json.load(f)

    assert saved_settings['statistics']['gpu_temp'] is False
    assert saved_settings['theme']['new_color'] == '#ff0000'

def test_get_settings_singleton():
    """get_settings fonksiyonunun bir singleton örneği döndürdüğünü test et."""
    instance1 = get_settings()
    instance2 = get_settings()

    assert instance1 is instance2

    instance1.set_setting('gpu_updates.check_enabled', False)
    assert instance2.get_setting('gpu_updates.check_enabled') is False
