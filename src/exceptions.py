"""
Custom exceptions for the Systemizer application.

This module defines specific exception types that can be raised and caught
in different parts of the application, leading to more robust error handling
and clearer code.
"""


class SystemizerError(Exception):
    """Base class for all custom exceptions in the Systemizer application."""
    pass


# --- GPU Monitoring Errors ---

class GpuMonitorError(SystemizerError):
    """Base exception for errors related to GPU monitoring."""
    pass


class NvidiaLibraryError(GpuMonitorError):
    """Raised when the pynvml (NVIDIA) library fails to initialize or is not found."""
    pass


class AmdLibraryError(GpuMonitorError):
    """Raised when the pyadl (AMD) library fails to initialize or is not found."""
    pass


# --- UI and Theme Errors ---

class ThemeError(SystemizerError):
    """Base exception for UI and theme-related errors."""
    pass


class ThemeNotFoundError(ThemeError, FileNotFoundError):
    """Raised when a theme file (e.g., theme.qss) cannot be found."""
    pass
