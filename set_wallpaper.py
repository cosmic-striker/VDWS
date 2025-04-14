import time
import ctypes
from pyvda import VirtualDesktop

# Map each virtual desktop number to a wallpaper path
# Note: Desktop indices from pyvda typically start at 1.
# In your mapping, index 0 is used for no wallpaper.
wallpapers = {
    0: r"",                # No wallpaper assigned for this index
    1: r"F:\projects\virtual_desktop_wallpaper_win10\wallpaper1.jpg",  # Ensure the file exists or provide a full path
    2: r"F:\projects\virtual_desktop_wallpaper_win10\wallpaper2.jpg"
}

# Constants used to change the wallpaper via the Windows API
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02

def set_wallpaper(image_path):
    """
    Change the desktop wallpaper using the SystemParametersInfoW API.
    If image_path is empty, a message is printed.
    """
    if image_path:
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path, SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
        if not result:
            print("Failed to update wallpaper for:", image_path)
    else:
        print("No wallpaper defined for this desktop.")

def main():
    current_desktop = None
    while True:
        try:
            # Get the current desktop using pyvda
            desktop = VirtualDesktop.current()
            index = desktop.number  # Current desktop number (usually starting at 1)
            
            # Change wallpaper only if desktop has changed
            if index != current_desktop:
                current_desktop = index
                print(f"Switched to virtual desktop {index}")
                # Get the wallpaper for the current desktop from the mapping,
                # or default to an empty string.
                wallpaper_path = wallpapers.get(index, r"")
                set_wallpaper(wallpaper_path)
        except Exception as e:
            print("Error:", e)
        
        # Wait 1 second before polling again
        time.sleep(1)

if __name__ == "__main__":
    main()