#!/usr/bin/env python3
"""
Intel GPU Driver Control System Test Suite
Tests compatibility and functionality for Intel graphics cards
"""

import sys
import os
import subprocess
import json
from typing import Dict, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_intel_detection() -> Tuple[bool, str]:
    """Test Intel GPU detection"""
    print("\n" + "="*60)
    print("TEST 1: Intel GPU Detection")
    print("="*60)
    
    try:
        from src.services.gpu_monitor import GPUMonitor
        monitor = GPUMonitor()
        
        print(f"Detected GPU Vendor: {monitor.vendor}")
        print(f"GPU Name: {monitor.gpu_name}")
        print(f"VRAM Total: {monitor.vram_total} MB")
        print(f"GPU Available: {monitor._gpu_available}")
        
        if monitor.vendor == "Intel":
            print("✓ Intel GPU detected successfully!")
            return True, f"Intel GPU: {monitor.gpu_name}"
        else:
            print(f"⚠ No Intel GPU detected. Found: {monitor.vendor}")
            return False, f"Found {monitor.vendor} instead of Intel"
    except Exception as e:
        print(f"✗ Error detecting Intel GPU: {e}")
        return False, str(e)

def test_intel_stats() -> Tuple[bool, str]:
    """Test Intel GPU statistics retrieval"""
    print("\n" + "="*60)
    print("TEST 2: Intel GPU Statistics")
    print("="*60)
    
    try:
        from src.services.gpu_monitor import GPUMonitor
        monitor = GPUMonitor()
        
        if monitor.vendor != "Intel":
            print(f"⚠ Skipping stats test - detected {monitor.vendor}, not Intel")
            return False, f"Not an Intel GPU system"
        
        stats = monitor.get_stats()
        
        if stats:
            print("Intel GPU Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            print("✓ Intel GPU statistics retrieved successfully!")
            return True, "Stats retrieved"
        else:
            print("✗ Failed to retrieve Intel GPU statistics")
            return False, "Stats returned None"
    except Exception as e:
        print(f"✗ Error getting Intel GPU stats: {e}")
        return False, str(e)

def test_intel_driver_detection() -> Tuple[bool, str]:
    """Test Intel driver version detection"""
    print("\n" + "="*60)
    print("TEST 3: Intel Driver Version Detection")
    print("="*60)
    
    try:
        from src.services.gpu_driver_updater import GPUDriverUpdater
        updater = GPUDriverUpdater()
        
        print(f"GPU Vendor: {updater.gpu_vendor}")
        print(f"Current Driver Version: {updater.current_driver_version}")
        
        if updater.gpu_vendor == "Intel":
            if updater.current_driver_version:
                print("✓ Intel driver version detected successfully!")
                return True, f"Intel driver v{updater.current_driver_version}"
            else:
                print("⚠ Intel GPU detected but driver version could not be retrieved")
                return False, "Driver version not found"
        else:
            print(f"⚠ No Intel driver detected. Found: {updater.gpu_vendor}")
            return False, f"Found {updater.gpu_vendor} instead"
    except Exception as e:
        print(f"✗ Error detecting Intel driver: {e}")
        return False, str(e)

def test_intel_update_check() -> Tuple[bool, str]:
    """Test Intel driver update checking"""
    print("\n" + "="*60)
    print("TEST 4: Intel Driver Update Check")
    print("="*60)
    
    try:
        from src.services.gpu_driver_updater import GPUDriverUpdater
        updater = GPUDriverUpdater()
        
        if updater.gpu_vendor != "Intel":
            print(f"⚠ Skipping update check - detected {updater.gpu_vendor}, not Intel")
            return False, f"Not an Intel driver system"
        
        result, latest = updater.check_for_updates()
        info = updater.get_update_info()
        
        print("Driver Update Check Results:")
        print(f"  Vendor: {info['vendor']}")
        print(f"  Current Version: {info['current_version']}")
        print(f"  Latest Version: {info['latest_version']}")
        print(f"  Update Available: {result}")
        print(f"  Last Check: {info['last_check']}")
        
        print("✓ Intel driver update check completed successfully!")
        return True, f"Latest: {latest or 'Unknown'}"
    except Exception as e:
        print(f"✗ Error checking Intel driver updates: {e}")
        return False, str(e)

def test_wmi_intel_queries() -> Tuple[bool, str]:
    """Test WMI queries for Intel GPU detection"""
    print("\n" + "="*60)
    print("TEST 5: WMI Intel GPU Queries")
    print("="*60)
    
    try:
        # Test device detection
        cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController -Filter \\"DeviceName LIKE \'%Intel%\'\\" | Select-Object -First 1 Caption, AdapterRAM | ConvertTo-Json"'
        output = subprocess.check_output(cmd, shell=True, timeout=10).decode('utf-8', errors='ignore').strip()
        
        if output:
            data = json.loads(output)
            print("Intel GPU Detection via WMI:")
            print(f"  Device Name: {data.get('Caption', 'Unknown')}")
            print(f"  VRAM: {data.get('AdapterRAM', 0)} bytes")
            print("✓ WMI Intel GPU detection working!")
            return True, f"WMI detected Intel GPU"
        else:
            print("⚠ No Intel GPU found via WMI")
            return False, "WMI did not find Intel GPU"
    except Exception as e:
        print(f"✗ Error in WMI Intel query: {e}")
        return False, str(e)

def test_wmi_intel_driver_version() -> Tuple[bool, str]:
    """Test WMI query for Intel driver version"""
    print("\n" + "="*60)
    print("TEST 6: WMI Intel Driver Version Query")
    print("="*60)
    
    try:
        cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PnPSignedDriver -Filter \\"DeviceName LIKE \'%Intel%Graphics%\'\\" | Select-Object -First 1 DriverVersion"'
        output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
        
        if output and 'DriverVersion' not in output:
            print(f"Intel Driver Version via WMI: {output}")
            print("✓ WMI Intel driver version query working!")
            return True, f"Driver version: {output}"
        else:
            print("⚠ Could not retrieve Intel driver version via WMI")
            return False, "WMI returned no driver version"
    except Exception as e:
        print(f"✗ Error in WMI driver version query: {e}")
        return False, str(e)

def run_all_tests() -> Dict[str, Tuple[bool, str]]:
    """Run all Intel compatibility tests"""
    print("\n")
    print("=" * 60)
    print("INTEL GPU DRIVER SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Intel GPU Detection", test_intel_detection),
        ("Intel GPU Statistics", test_intel_stats),
        ("Intel Driver Detection", test_intel_driver_detection),
        ("Intel Update Check", test_intel_update_check),
        ("WMI Intel Queries", test_wmi_intel_queries),
        ("WMI Driver Version", test_wmi_intel_driver_version),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results[test_name] = (success, message)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results[test_name] = (False, str(e))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    
    for test_name, (success, message) in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        print(f"       {message}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("-"*60)
    
    if passed == total:
        print("✓ All tests passed! Intel GPU support is fully functional.")
        return_code = 0
    elif passed >= total * 0.5:
        print("⚠ Some tests failed. Intel GPU support may be partially functional.")
        return_code = 1
    else:
        print("✗ Most tests failed. Intel GPU support needs attention.")
        return_code = 2
    
    return results, return_code

if __name__ == "__main__":
    try:
        results, return_code = run_all_tests()
        sys.exit(return_code)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
