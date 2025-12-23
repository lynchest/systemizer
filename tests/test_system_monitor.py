import pytest
from unittest.mock import MagicMock

# --- Top-Level Import ---
# Import the module to be tested at the top level of the test file.
# This ensures that the module and its contents (like the 'psutil' object we
# want to mock) are loaded into memory *before* pytest tries to set up the
# fixtures that patch it. This resolves the `AttributeError` during test setup.
from services.system_monitor import SystemMonitor


# --- Test Fixtures ---

@pytest.fixture
def mock_psutil(mocker):
    """
    Mocks the `psutil` library to prevent real system calls during tests.
    """
    mock = MagicMock()
    # Mock return values for all psutil functions used in SystemMonitor
    mock.cpu_percent.side_effect = [10.0, [5.0, 15.0]]
    mock.virtual_memory.return_value = MagicMock(total=16*1024**3, used=8*1024**3, percent=50.0)
    mock.swap_memory.return_value = MagicMock(total=8*1024**3, used=2*1024**3, percent=25.0)
    mock.disk_usage.return_value = MagicMock(total=512*1024**3, used=256*1024**3, percent=50.0)
    mock.net_io_counters.return_value = MagicMock(bytes_sent=1024*1024*100, bytes_recv=1024*1024*500)
    mock.boot_time.return_value = 1672531200
    mock.pids.return_value = list(range(5))

    # The target string for patching must point to where the object is *used*.
    mocker.patch('services.system_monitor.psutil', mock)
    return mock


@pytest.fixture
def mock_subprocess(mocker):
    """Mocks `subprocess.check_output` to avoid running PowerShell."""
    mock = mocker.patch('subprocess.check_output')
    mock.return_value.decode.return_value.strip.return_value = "3200\n3200"
    return mock


# --- Test Cases ---

def test_system_monitor_initialization(mock_psutil, mock_subprocess):
    """
    Tests if the SystemMonitor initializes correctly, caching necessary info.
    """
    # SystemMonitor is already imported at the top level
    monitor = SystemMonitor()

    # Verify that psutil functions were called during initialization
    mock_psutil.boot_time.assert_called_once()
    mock_psutil.virtual_memory.assert_called_once()
    mock_subprocess.assert_called_once()

    # Check if cached values are correct (16 GB total memory)
    assert monitor._total_mem_gb == 16.0
    assert monitor.get_ram_speed_info() == "3200 MHz"


def test_get_cpu_stats(mock_psutil, mock_subprocess):
    """Tests the CPU statistics retrieval."""
    monitor = SystemMonitor()
    stats = monitor.get_cpu_stats()

    assert stats["total_usage"] == 10.0
    assert stats["per_core"] == [5.0, 15.0]
    assert mock_psutil.cpu_percent.call_count == 2


def test_get_memory_stats(mock_psutil, mock_subprocess):
    """Tests the Memory statistics retrieval."""
    monitor = SystemMonitor()
    stats = monitor.get_memory_stats()

    assert stats["total"] == 16.0
    assert stats["used"] == 8.0
    assert stats["percent"] == 50.0
    assert stats["swap_percent"] == 25.0


def test_get_disk_stats(mock_psutil, mock_subprocess):
    """Tests the Disk statistics retrieval."""
    monitor = SystemMonitor()
    stats = monitor.get_disk_stats()

    mock_psutil.disk_usage.assert_called_with('C:\\')
    assert stats["total"] == 512.0
    assert stats["percent"] == 50.0


def test_get_process_stats(mock_psutil, mock_subprocess):
    """Tests the process count retrieval."""
    monitor = SystemMonitor()
    count = monitor.get_process_stats()

    mock_psutil.pids.assert_called_once()
    assert count == 5
