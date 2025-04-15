import time
import ctypes
import curses
from pyvda import VirtualDesktop

# Dictionary mapping desktop number -> wallpaper path.
wallpapers = {
    0: r"",  # No wallpaper for desktop 0 (example)
    1: r"F:\projects\virtual_desktop_wallpaper_win10\wallpaper1.jpg",
    2: r"F:\projects\virtual_desktop_wallpaper_win10\wallpaper2.jpg"
}

# Windows API constants for changing wallpaper.
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02

# Global flag to enable/disable wallpaper switching.
enabled = True

ASCII_BANNER = r"""
,---.  ,---. ______     .--.      .--.   .-'''-.  ________ .--.      .--..-./`) ,---.   .--. .---.  .-```````-.  
|   /  |   ||    _ `''. |  |_     |  |  / _     \|        ||  |_     |  |\ .-.')|    \  |  | \   / / ,```````. \ 
|  |   |  .'| _ | ) _  \| _( )_   |  | (`' )/`--'|   .----'| _( )_   |  |/ `-' \|  ,  \ |  | |   | |/ .-./ )  \| 
|  | _ |  | |( ''_'  ) ||(_ o _)  |  |(_ o _).   |  _|____ |(_ o _)  |  | `-'`"`|  |\_ \|  |  \ /  || \ '_ .')|| 
|  _( )_  | | . (_) `. || (_,_) \ |  | (_,_). '. |_( )_   || (_,_) \ |  | .---. |  _( )_\  |   v   ||(_ (_) _)|| 
\ (_ o._) / |(_    ._) '|  |/    \|  |.---.  \  :(_ o._)__||  |/    \|  | |   | | (_ o _)  |  _ _  ||  / .  \ || 
 \ (_,_) /  |  (_.\.' / |  '  /\  `  |\    `-'  ||(_,_)    |  '  /\  `  | |   | |  (_,_)\  | (_I_) ||  `-'`"` || 
  \     /   |       .'  |    /  \    | \       / |   |     |    /  \    | |   | |  |    |  |(_(=)_)\'._______.'/ 
   `---`    '-----'`    `---'    `---`  `-...-'  '---'     `---'    `---` '---' '--'    '--' (_I_)  '._______.'  
           
                                                                                                                 
                /_/   v1.0  (VDWSFWin!0)                      
Coded by You  |  Example Terminal Interface  |  UTF-8/ASCII
"""

def set_wallpaper(image_path):
    """
    Use the Windows API to change the desktop wallpaper.
    """
    if image_path:
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
        )
        if not result:
            return f"[!] Failed to update wallpaper: {image_path}"
        return f"[+] Wallpaper updated to: {image_path}"
    else:
        return "[!] No wallpaper defined for this desktop."

def curses_input(stdscr, prompt, y, x):
    """
    Prompt the user for input in curses.
    """
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    # Read up to 60 characters
    input_str = stdscr.getstr(y, x + len(prompt), 60).decode("utf-8", errors="replace")
    curses.noecho()
    return input_str

def main_curses(stdscr):
    global enabled, wallpapers

    curses.curs_set(0)      # Hide the cursor.
    stdscr.nodelay(True)    # Non-blocking input.
    stdscr.timeout(500)     # Refresh every 500 ms.

    current_desktop = None
    search_counter = 0  # Just for the "Searching" mimic.

    while True:
        stdscr.clear()

        # Print the ASCII banner at the top
        for i, line in enumerate(ASCII_BANNER.split('\n')):
            stdscr.addstr(i, 0, line)

        row_offset = ASCII_BANNER.count('\n') + 1
        stdscr.addstr(row_offset, 0, "[q] Quit  |  [p] Toggle Enabled/Disabled  |  [c] Change Wallpaper")
        stdscr.addstr(row_offset + 1, 0, "[a] Add Mapping | [d] Delete Mapping")

        # Show current status
        status_line = f"Wallpaper auto-update is: {'ENABLED' if enabled else 'DISABLED'}"
        stdscr.addstr(row_offset + 3, 0, status_line)

        # Show current mappings
        stdscr.addstr(row_offset + 5, 0, "Current Wallpaper Mappings:")
        line = row_offset + 6
        for d_num, w_path in sorted(wallpapers.items()):
            stdscr.addstr(line, 2, f"Desktop {d_num}: {w_path or '(no wallpaper)'}")
            line += 1

        # Attempt to detect the current desktop and update wallpaper if enabled.
        try:
            desktop = VirtualDesktop.current()
            idx = desktop.number
            stdscr.addstr(line + 1, 0, f"[-] Current Virtual Desktop: {idx}")
            
            # Auto-update wallpaper if there's a change in desktop and it's enabled.
            if enabled and (idx != current_desktop):
                current_desktop = idx
                wallpaper_path = wallpapers.get(idx, "")
                result_msg = set_wallpaper(wallpaper_path)
                stdscr.addstr(line + 2, 0, result_msg)
        except Exception as e:
            stdscr.addstr(line + 3, 0, "[Error] " + str(e))

        # Mimic a "searching" or "scan" style for flavor
        searching_msg = f"[-] Searching {search_counter} results..."
        stdscr.addstr(line + 5, 0, searching_msg)
        search_counter += 100  # Increase in increments to mimic scanning
        if search_counter > 1000:  # reset for demonstration
            search_counter = 0

        stdscr.refresh()

        # Grab user input
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == ord('q'):
            break  # Quit
        elif key == ord('p'):
            enabled = not enabled
        elif key == ord('c'):
            # Change wallpaper for a specific desktop
            stdscr.nodelay(False)
            idx_str = curses_input(stdscr, "Enter desktop number to change: ", line + 7, 0)
            try:
                desk_idx = int(idx_str)
            except ValueError:
                stdscr.addstr(line + 8, 0, "[!] Invalid number. Press any key.")
                stdscr.getch()
                stdscr.nodelay(True)
                continue
            path = curses_input(stdscr, "Enter new wallpaper path: ", line + 9, 0)
            wallpapers[desk_idx] = path
            stdscr.addstr(line + 10, 0, f"[+] Desktop {desk_idx} wallpaper changed to: {path}")
            stdscr.getch()
            stdscr.nodelay(True)
        elif key == ord('a'):
            # Add a new mapping
            stdscr.nodelay(False)
            idx_str = curses_input(stdscr, "Enter new desktop number: ", line + 7, 0)
            try:
                desk_idx = int(idx_str)
            except ValueError:
                stdscr.addstr(line + 8, 0, "[!] Invalid number. Press any key.")
                stdscr.getch()
                stdscr.nodelay(True)
                continue
            if desk_idx in wallpapers:
                stdscr.addstr(line + 8, 0, "[!] Mapping exists. Use 'Change' instead. Press any key.")
                stdscr.getch()
                stdscr.nodelay(True)
                continue
            path = curses_input(stdscr, "Enter new wallpaper path: ", line + 9, 0)
            wallpapers[desk_idx] = path
            stdscr.addstr(line + 10, 0, f"[+] Added: Desktop {desk_idx} -> {path}")
            stdscr.getch()
            stdscr.nodelay(True)
        elif key == ord('d'):
            # Delete a mapping
            stdscr.nodelay(False)
            idx_str = curses_input(stdscr, "Enter desktop number to delete: ", line + 7, 0)
            try:
                desk_idx = int(idx_str)
            except ValueError:
                stdscr.addstr(line + 8, 0, "[!] Invalid number. Press any key.")
                stdscr.getch()
                stdscr.nodelay(True)
                continue
            if desk_idx in wallpapers:
                del wallpapers[desk_idx]
                stdscr.addstr(line + 8, 0, f"[+] Deleted mapping for desktop {desk_idx}. Press any key.")
            else:
                stdscr.addstr(line + 8, 0, f"[!] No mapping found for desktop {desk_idx}. Press any key.")
            stdscr.getch()
            stdscr.nodelay(True)

        time.sleep(0.1)

if __name__ == "__main__":
    curses.wrapper(main_curses)
