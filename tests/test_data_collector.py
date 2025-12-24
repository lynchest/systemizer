import pytest
from unittest.mock import MagicMock, patch

# PySide6'yı en üst seviyede içe aktarma

@pytest.fixture
def collector_and_mocks():
    """Test için taklit edilmiş bir DataCollectorThread örneği ayarlar."""
    # PySide6'yı ve MockQThread'i fikstür içinde içe aktar ve tanımla
    from PySide6.QtCore import QObject
    from src.services.data_collector import DataCollectorThread

    class MockQThread(QObject):
        def __init__(self): super().__init__()
        def start(self): pass
        def quit(self): pass
        def wait(self): pass

    # DataCollectorThread örneği oluşturulmadan önce QThread'i yama
    with patch('src.services.data_collector.QThread', MockQThread), \
         patch('src.services.data_collector.GPUMonitor') as mock_gpu_monitor, \
         patch('src.services.data_collector.SystemMonitor') as mock_system_monitor, \
         patch('src.services.data_collector.get_settings') as mock_get_settings:

        # Ayarları taklit et
        mock_settings = MagicMock()
        mock_settings.get_all_statistics.return_value = {
            'cpu': True, 'cpu_cores': True, 'ram': True, 'ram_speed': True,
            'net_down': True, 'net_up': True, 'processes': True, 'disk': True,
            'uptime': True, 'gpu': True, 'vram': True, 'gpu_temp': True,
            'gpu_power': True, 'gpu_fan': True, 'gpu_clock': True
        }
        mock_get_settings.return_value = mock_settings

        # Monitörleri taklit et
        mock_sys_monitor_instance = mock_system_monitor.return_value
        mock_gpu_monitor_instance = mock_gpu_monitor.return_value

        # SystemMonitor için taklit dönüş değerlerini ayarla
        mock_sys_monitor_instance.get_cpu_stats.return_value = {'total_usage': 50, 'per_core': [40, 60]}
        mock_sys_monitor_instance.get_memory_stats.return_value = {'percent': 75, 'used': 12, 'total': 16}
        mock_sys_monitor_instance.get_network_stats.return_value = {'bytes_recv': 10240, 'bytes_sent': 5120}
        mock_sys_monitor_instance.get_ram_speed_info.return_value = 3200
        mock_sys_monitor_instance.get_process_stats.return_value = 150
        mock_sys_monitor_instance.get_disk_stats.return_value = {'percent': 60}
        mock_sys_monitor_instance.get_uptime.return_value = 7260  # 2 saat 1 dakika

        # GPUMonitor için taklit dönüş değerlerini ayarla
        mock_gpu_monitor_instance.get_stats.return_value = {
            'gpu_usage': 80, 'vram_used': 4096, 'vram_total': 8192,
            'vram_percent': 50, 'temp': 65, 'power_draw': 120,
            'fan_speed': 1500, 'core_clock': 1800
        }
        mock_gpu_monitor_instance._gpu_available = True

        # Test edilen sınıfı örneklendir
        collector = DataCollectorThread()
        collector.last_net_recv = 0
        collector.last_net_sent = 0

        yield collector, mock_gpu_monitor_instance

def test_collect_fast_data(collector_and_mocks):
    """_collect_fast_data fonksiyonunu test eder."""
    collector, _ = collector_and_mocks
    fast_data = collector._collect_fast_data()

    assert fast_data is not None
    assert fast_data['cpu_usage'] == 50
    assert fast_data['cpu_cores'] == 2
    assert fast_data['ram_percent'] == 75
    assert fast_data['ram_used'] == 12
    assert fast_data['ram_total'] == 16
    assert fast_data['ram_speed'] == 3200
    assert fast_data['net_down_speed'] == 10.0
    assert fast_data['net_up_speed'] == 5.0

def test_collect_medium_data(collector_and_mocks):
    """_collect_medium_data fonksiyonunu test eder."""
    collector, _ = collector_and_mocks
    medium_data = collector._collect_medium_data()

    assert medium_data is not None
    assert medium_data['process_count'] == 150

def test_collect_slow_data(collector_and_mocks):
    """_collect_slow_data fonksiyonunu test eder."""
    collector, _ = collector_and_mocks
    slow_data = collector._collect_slow_data()

    assert slow_data is not None
    assert slow_data['disk_percent'] == 60
    assert slow_data['uptime_hours'] == 2
    assert slow_data['uptime_minutes'] == 1

def test_collect_gpu_data_available(collector_and_mocks):
    """GPU mevcut olduğunda _collect_gpu_data'yı test eder."""
    collector, _ = collector_and_mocks
    gpu_data = collector._collect_gpu_data()

    assert gpu_data is not None
    assert gpu_data['available'] is True
    assert gpu_data['gpu_usage'] == 80
    assert gpu_data['vram_used'] == 4
    assert gpu_data['vram_total'] == 8
    assert gpu_data['vram_percent'] == 50
    assert gpu_data['temp'] == 65
    assert gpu_data['power_draw'] == 120
    assert gpu_data['fan_speed'] == 1500
    assert gpu_data['core_clock'] == 1800

def test_collect_gpu_data_unavailable(collector_and_mocks):
    """GPU mevcut olmadığında _collect_gpu_data'yı test eder."""
    collector, mock_gpu_monitor = collector_and_mocks
    mock_gpu_monitor.get_stats.return_value = None
    collector.has_gpu = False

    gpu_data = collector._collect_gpu_data()

    assert gpu_data is not None
    assert gpu_data['available'] is False

def test_statistic_disabled(collector_and_mocks):
    """Devre dışı bırakılmış istatistikler için veri toplanmadığını test eder."""
    collector, _ = collector_and_mocks

    collector.set_statistic_enabled('cpu', False)
    fast_data = collector._collect_fast_data()
    assert 'cpu_usage' not in fast_data

    collector.set_statistic_enabled('processes', False)
    medium_data = collector._collect_medium_data()
    assert medium_data is None

    collector.set_statistic_enabled('disk', False)
    slow_data = collector._collect_slow_data()
    assert 'disk_percent' not in slow_data
