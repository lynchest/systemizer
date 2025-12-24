import pytest
from unittest.mock import patch, MagicMock
import json
import sys

# pynvml ve pyadl'nin sahte versiyonlarını oluştur
sys.modules['pynvml'] = MagicMock()
sys.modules['pyadl'] = MagicMock()

@pytest.fixture
def mock_pynvml():
    """pynvml kütüphanesi için bir taklit fikstürü."""
    mock = MagicMock()
    mock.nvmlInit.return_value = None
    mock.nvmlDeviceGetCount.return_value = 1
    mock.nvmlDeviceGetHandleByIndex.return_value = "mock_handle"
    mock.nvmlDeviceGetName.return_value = b"NVIDIA GeForce RTX 3080"

    mem_info = MagicMock()
    mem_info.total = 10240 * 1024**2
    mem_info.used = 2048 * 1024**2
    mock.nvmlDeviceGetMemoryInfo.return_value = mem_info

    return mock

@pytest.fixture
def monitor(request):
    """Her test için GPUMonitor'ı başlatan ve temizleyen bir fikstür."""
    # GPUMonitor'ı fikstürün içinde içe aktar
    from src.services.gpu_monitor import GPUMonitor

    # Singleton'ı sıfırla
    GPUMonitor._instance = None
    GPUMonitor._initialized = False

    # Fikstüre parametre olarak yama geçilmişse, onu uygula
    if hasattr(request, 'param'):
        with request.param:
            yield GPUMonitor()
    else:
        yield GPUMonitor()

# subprocess.check_output'ı taklit eden yamaları parametreleştir
@pytest.mark.parametrize('monitor', [
    patch('subprocess.check_output', return_value=json.dumps({"Caption": "NVIDIA GeForce"}).encode())
], indirect=True)
def test_init_nvidia(monitor, mock_pynvml):
    """NVIDIA GPU'sunun doğru bir şekilde başlatıldığını test et."""
    with patch('src.services.gpu_monitor.pynvml', mock_pynvml):
        monitor._init_nvidia()
        assert monitor.vendor == "NVIDIA"
        assert "Nvidia GeForce" in monitor.gpu_name
        assert monitor._gpu_available is True

@patch('subprocess.check_output', return_value=json.dumps({"Caption": "AMD Radeon"}).encode())
@patch('src.services.gpu_monitor.HAS_PYADL', True)
@patch('src.services.gpu_monitor.ADLManager')
def test_init_amd(mock_adl_manager, mock_subprocess, monitor):
    """AMD GPU'sunun pyadl ile doğru bir şekilde başlatıldığını test et."""
    mock_device = MagicMock()
    mock_device.adapterName = b"AMD Radeon RX 6800"
    mock_adl_manager.getInstance.return_value.getDevices.return_value = [mock_device]

    monitor._init_amd()
    assert "AMD Radeon" in monitor.gpu_name
    assert monitor._gpu_available is True

def test_sanitize_name():
    """GPU adının doğru bir şekilde temizlendiğini test et."""
    # Test için geçici bir monitör örneği oluştur
    from src.services.gpu_monitor import GPUMonitor
    monitor_instance = GPUMonitor()

    assert monitor_instance._sanitize_name("NVIDIA GeForce RTX™ 3080 (R)") == "Nvidia GeForce RTX 3080"
    assert monitor_instance._sanitize_name("   AMD   Radeon   ") == "AMD Radeon"
