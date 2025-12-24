"""
Test for version checking functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.version_checker import VersionChecker
from src.services.gpu_driver_updater import GPUDriverUpdater

def test_version_checker():
    """Test the version checker singleton"""
    print("Testing VersionChecker...")
    
    vc = VersionChecker()
    print(f"Current version: {vc.current_version}")
    print(f"GitHub releases URL: {vc.get_releases_url()}")
    
    # Check for updates
    print("\nChecking for application updates...")
    update_available, latest_version = vc.check_for_updates()
    print(f"Update available: {update_available}")
    print(f"Latest version: {latest_version}")
    
    # Get update info
    info = vc.get_update_info()
    print("\nUpdate info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

def test_gpu_driver_updater_integration():
    """Test GPU driver updater with version checker integration"""
    print("\n\nTesting GPU Driver Updater integration...")
    
    updater = GPUDriverUpdater()
    
    # Get all update info
    print("\nGetting all update info...")
    all_info = updater.get_all_update_info()
    
    print("\nDriver Update Info:")
    for key, value in all_info['driver'].items():
        print(f"  {key}: {value}")
    
    print("\nApplication Update Info:")
    for key, value in all_info['application'].items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_version_checker()
    test_gpu_driver_updater_integration()
