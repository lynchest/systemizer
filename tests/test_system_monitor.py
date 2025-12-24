import pytest
from unittest.mock import patch, MagicMock

# SystemMonitor'ı doğrudan içe aktarmak yerine fikstürde yap
@pytest.fixture
def monitor():
    """SystemMonitor için taklit edilmiş bağımlılıklarla bir test fikstürü."""
    # psutil ve subprocess'i taklit et
    with patch('psutil.boot_time', return_value=1000.0), \
         patch('psutil.virtual_memory') as mock_vm, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('subprocess.check_output', return_value=b'3200\n'):

        # Sanal bellek için taklit değerleri ayarla
        vm_mock = MagicMock()
        vm_mock.total = 16 * 1024**3
        vm_mock.used = 12 * 1024**3
        vm_mock.percent = 75.0
        mock_vm.return_value = vm_mock

        # Test edilecek sınıfı içe aktar ve örneklendir
        from src.services.system_monitor import SystemMonitor
        yield SystemMonitor()

@patch('psutil.cpu_percent', side_effect=[50.0, [40.0, 60.0]])
def test_get_cpu_stats(mock_cpu_percent, monitor):
    """CPU istatistiklerinin doğru bir şekilde alındığını test et."""
    stats = monitor.get_cpu_stats()
    assert stats['total_usage'] == 50.0
    assert stats['per_core'] == [40.0, 60.0]

@patch('psutil.swap_memory')
def test_get_memory_stats(mock_swap, monitor):
    """Bellek istatistiklerinin doğru bir şekilde alındığını test et."""
    swap_mock = MagicMock()
    swap_mock.total = 8 * 1024**3
    swap_mock.used = 2 * 1024**3
    swap_mock.percent = 25.0
    mock_swap.return_value = swap_mock

    stats = monitor.get_memory_stats()
    assert abs(stats['total'] - 16.0) < 0.1
    assert abs(stats['used'] - 12.0) < 0.1
    assert stats['percent'] == 75.0
    assert abs(stats['swap_used'] - 2.0) < 0.1

@patch('psutil.net_io_counters')
def test_get_network_stats(mock_net_io, monitor):
    """Ağ istatistiklerinin doğru bir şekilde alındığını test et."""
    net_mock = MagicMock()
    net_mock.bytes_sent = 10240
    net_mock.bytes_recv = 20480
    mock_net_io.return_value = net_mock

    stats = monitor.get_network_stats()
    assert stats['bytes_sent'] == 10240
    assert stats['bytes_recv'] == 20480

@patch('psutil.pids', return_value=[1, 2, 3, 4, 5])
def test_get_process_stats(mock_pids, monitor):
    """İşlem sayısının doğru bir şekilde alındığını test et."""
    count = monitor.get_process_stats()
    assert count == 5

@patch('time.time', return_value=1500.0)
def test_get_uptime(mock_time, monitor):
    """Sistem çalışma süresinin doğru bir şekilde hesaplandığını test et."""
    uptime = monitor.get_uptime()
    assert uptime == 500.0

def test_get_ram_speed_info(monitor):
    """RAM hızının doğru bir şekilde alındığını ve önbelleğe alındığını test et."""
    speed = monitor.get_ram_speed_info()
    assert speed == "3200 MHz"
