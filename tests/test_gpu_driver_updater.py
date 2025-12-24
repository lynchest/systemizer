import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# GPUDriverUpdater'ı test fonksiyonlarının içinde içe aktarılacak şekilde ayarla

@pytest.fixture
def updater():
    """Her testten önce GPUDriverUpdater singleton'ını sıfırlayan bir fikstür."""
    # Test edilecek sınıfı içe aktar
    from src.services.gpu_driver_updater import GPUDriverUpdater

    # Singleton'ı sıfırlayarak testlerin birbirinden izole olmasını sağla
    GPUDriverUpdater._instance = None
    GPUDriverUpdater._initialized = False
    yield GPUDriverUpdater()

@patch('subprocess.check_output')
def test_detect_nvidia_driver(mock_subprocess, updater):
    """NVIDIA sürücüsünün doğru bir şekilde algılandığını test et."""
    mock_subprocess.side_effect = [
        b'512.15\n', # nvidia-smi başarılı
        Exception("AMD not found"),
        Exception("Intel not found")
    ]
    updater._detect_driver_version()
    assert updater.gpu_vendor == "NVIDIA"
    assert updater.current_driver_version == "512.15"

@patch('subprocess.check_output')
def test_detect_amd_driver(mock_subprocess, updater):
    """AMD sürücüsünün doğru bir şekilde algılandığını test et."""
    mock_subprocess.side_effect = [
        Exception("NVIDIA not found"),
        b'22.5.1\n' # AMD PowerShell başarılı
    ]
    updater._detect_driver_version()
    assert updater.gpu_vendor == "AMD"
    assert updater.current_driver_version == "22.5.1"

def test_compare_versions(updater):
    """Sürüm karşılaştırma mantığını test et."""
    assert updater._compare_versions("512.15", "512.77")
    assert not updater._compare_versions("512.77", "512.15")
    assert updater._compare_versions("22.5.1", "22.11.2")
    assert not updater._compare_versions("22.11.2", "22.5.1")

@patch('requests.get')
@patch('subprocess.check_output')
def test_nvidia_update_available(mock_subprocess, mock_requests, updater):
    """NVIDIA için bir güncelleme mevcut olduğunda doğrula."""
    mock_subprocess.return_value = b'512.15\n'
    updater.gpu_vendor = "NVIDIA"
    updater.current_driver_version = "512.15"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"DriverVersion": "512.77"}
    mock_requests.return_value = mock_response

    update_available, latest_version = updater.check_for_updates()

    assert update_available is True
    assert latest_version == "512.77"

def test_callback_notification(updater):
    """Callback fonksiyonlarının doğru şekilde çağrıldığını test et."""
    mock_callback = MagicMock()
    updater.register_callback(mock_callback)
    updater._notify_callbacks(True, "1.2.3")
    mock_callback.assert_called_once_with(True, "1.2.3")

    updater.unregister_callback(mock_callback)
    assert mock_callback not in updater.update_callbacks
