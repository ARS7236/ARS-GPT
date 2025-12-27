import winreg
import sys

def get_windows_accent_color():
    """
    Reads the Windows accent color from the registry.
    Returns the color in #RRGGBB format or None if not found.
    """
    if sys.platform != 'win32':
        return None

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
        value, _ = winreg.QueryValueEx(key, "AccentColor")
        winreg.CloseKey(key)

        # The color is in AABBGGRR format, convert to #RRGGBB
        abgr = f"{value:08x}"
        #blue = abgr[2:4]
        #green = abgr[4:6]
        #red = abgr[6:8]
        #return f"#{red}{green}{blue}"
        # The color is in AABBGGRR format, we need to extract R, G, B
        b = (value >> 16) & 0xFF
        g = (value >> 8) & 0xFF
        r = value & 0xFF
        return f'#{r:02x}{g:02x}{b:02x}'

    except FileNotFoundError:
        return None
