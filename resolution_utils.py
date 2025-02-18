import ctypes
import platform

# Define DEVMODEW structure for Windows
class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmOrientation", ctypes.c_short),
        ("dmPaperSize", ctypes.c_short),
        ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short),
        ("dmScale", ctypes.c_short),
        ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short),
        ("dmPrintQuality", ctypes.c_short),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_short),
        ("dmBitsPerPel", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_ulong),
        ("dmPelsHeight", ctypes.c_ulong),
        ("dmDisplayFlags", ctypes.c_ulong),
        ("dmDisplayFrequency", ctypes.c_ulong),
        ("dmICMMethod", ctypes.c_ulong),
        ("dmICMIntent", ctypes.c_ulong),
        ("dmMediaType", ctypes.c_ulong),
        ("dmDitherType", ctypes.c_ulong),
        ("dmReserved1", ctypes.c_ulong),
        ("dmReserved2", ctypes.c_ulong),
        ("dmPanningWidth", ctypes.c_ulong),
        ("dmPanningHeight", ctypes.c_ulong),
    ]

def change_resolution_refresh(width, height, refresh_rate):
    """Changes the screen resolution and refresh rate."""
    if platform.system() == "Windows":
        try:
            user32 = ctypes.windll.user32
            devmode = DEVMODEW()
            devmode.dmSize = ctypes.sizeof(DEVMODEW)
            devmode.dmPelsWidth = width
            devmode.dmPelsHeight = height
            devmode.dmDisplayFrequency = refresh_rate
            # Set dmFields to specify which members to use:
            # DM_PELSWIDTH (0x80000), DM_PELSHEIGHT (0x100000), DM_DISPLAYFREQUENCY (0x400000)
            devmode.dmFields = 0x80000 | 0x100000 | 0x400000
            result = user32.ChangeDisplaySettingsW(ctypes.byref(devmode), 0)
            if result == 0:  # DISP_CHANGE_SUCCESSFUL
                return True
            else:
                return False
        except Exception as e:
            print(f"Error changing resolution/refresh rate: {e}")
            return False
    else:
        print("This function is only supported on Windows.")
        return False

def reset_resolution_refresh():
    """Resets the screen resolution and refresh rate to the default."""
    if platform.system() == "Windows":
        try:
            user32 = ctypes.windll.user32
            result = user32.ChangeDisplaySettingsW(None, 0)  # None resets to default.
            if result == 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error resetting resolution/refresh rate: {e}")
            return False
    else:
        print("This function is only supported on Windows.")
        return False

def get_current_resolution_refresh():
    """Gets the current screen resolution and refresh rate."""
    if platform.system() == "Windows":
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        devmode = DEVMODEW()
        devmode.dmSize = ctypes.sizeof(DEVMODEW)
        devmode.dmDriverExtra = 0
        user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode))  # Get current setting.
        refresh = devmode.dmDisplayFrequency
        return width, height, refresh
    else:
        return None, None, None
