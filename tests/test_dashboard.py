import pytest
from unittest.mock import patch, MagicMock

# QApplication manuel olarak oluşturulmaz
# DashboardPage'i doğrudan içe aktarmak yerine fikstür içinde yap
@pytest.fixture(autouse=True)
def mock_services():
    with patch('src.ui.pages.dashboard.GPUMonitor') as mock_gpu_monitor, \
         patch('src.ui.pages.dashboard.SystemMonitor') as mock_sys_monitor, \
         patch('src.ui.pages.dashboard.DataCollectorThread') as mock_data_thread, \
         patch('src.ui.pages.dashboard.GPUDriverUpdater') as mock_driver_updater, \
         patch('src.ui.pages.dashboard.get_settings') as mock_get_settings:

        mock_gpu_monitor.return_value.gpu_name = "Mock GPU"
        mock_sys_monitor.return_value.get_cpu_stats.return_value = {'per_core': [0, 0, 0, 0]}

        mock_settings_instance = MagicMock()
        mock_settings_instance.is_statistic_enabled.return_value = True
        mock_get_settings.return_value = mock_settings_instance

        yield {
            "gpu_monitor": mock_gpu_monitor,
            "sys_monitor": mock_sys_monitor,
            "data_thread": mock_data_thread,
            "driver_updater": mock_driver_updater,
            "settings": mock_settings_instance
        }

@pytest.fixture
def dashboard(qtbot, mock_services):
    """Dashboard sayfası için bir test fikstürü oluştur."""
    # DashboardPage'i fikstürün içinde içe aktar
    from src.ui.pages.dashboard import DashboardPage

    page = DashboardPage()
    qtbot.addWidget(page)
    page.data_thread = mock_services['data_thread'].return_value
    yield page, mock_services

def test_dashboard_init(dashboard):
    """Dashboard sayfasının doğru bir şekilde başlatıldığını test et."""
    page, mocks = dashboard

    assert 'cpu' in page.cards
    assert 'gpu' in page.cards
    assert 'disk' in page.cards

    mocks['data_thread'].return_value.start.assert_called_once()
    mocks['driver_updater'].return_value.check_for_updates_async.assert_called_once()

def test_on_fast_update(dashboard):
    """Hızlı veri güncellemelerinin kartları doğru şekilde güncellediğini test et."""
    page, mocks = dashboard

    test_data = {
        'cpu_usage': 55.5,
        'ram_percent': 75.1,
        'ram_used': 12.0,
        'ram_total': 16.0,
        'net_down_speed': 1024.0, # 1.0 MB/s
    }

    with patch.object(page.cards['cpu'], 'update_value') as mock_update_cpu, \
         patch.object(page.cards['ram'], 'update_value') as mock_update_ram, \
         patch.object(page.cards['net_down'], 'update_value') as mock_update_net:

        page._on_fast_update(test_data)

        mock_update_cpu.assert_called_once_with("55%", 55)
        mock_update_ram.assert_called_once_with("75%", 75, "12.0 / 16.0 GB")
        mock_update_net.assert_called_once_with("1.0 MB/s", 10)

def test_on_gpu_update_unavailable(dashboard):
    """GPU mevcut olmadığında GPU kartlarının 'N/A' olarak ayarlandığını test et."""
    page, _ = dashboard

    with patch.object(page.cards['gpu'], 'update_value') as mock_update_gpu, \
         patch.object(page.cards['vram'], 'update_value') as mock_update_vram:

        page._on_gpu_update({'available': False})

        mock_update_gpu.assert_called_once_with("N/A", 0)
        mock_update_vram.assert_called_once_with("N/A", 0)

def test_refresh_visibility(dashboard):
    """refresh_visibility fonksiyonunun kart görünürlüğünü ayarlara göre güncellediğini test et."""
    page, mocks = dashboard

    mocks['settings'].is_statistic_enabled.side_effect = lambda key: key != 'cpu'

    with patch.object(page.cards['cpu'], 'setVisible') as mock_set_visible_cpu, \
         patch.object(page.cards['gpu'], 'setVisible') as mock_set_visible_gpu:

        page.refresh_visibility()

        mock_set_visible_cpu.assert_called_once_with(False)
        mock_set_visible_gpu.assert_called_once_with(True)
        mocks['data_thread'].return_value.set_statistic_enabled.assert_any_call('cpu', False)
        mocks['data_thread'].return_value.set_statistic_enabled.assert_any_call('gpu', True)

def test_on_section_toggled(dashboard):
    """Bir bölümün açılıp kapanmasının veri toplamayı doğru şekilde kontrol ettiğini test et."""
    page, mocks = dashboard

    page._on_section_toggled('gpu', False)

    gpu_stats = ['gpu', 'vram', 'gpu_temp', 'gpu_power', 'gpu_fan', 'gpu_clock']
    for stat in gpu_stats:
        mocks['data_thread'].return_value.set_statistic_enabled.assert_any_call(stat, False)

    page._on_section_toggled('gpu', True)

    for stat in gpu_stats:
        mocks['data_thread'].return_value.set_statistic_enabled.assert_any_call(stat, True)
