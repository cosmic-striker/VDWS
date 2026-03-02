import time
import ctypes
import curses
import os
import sys
from pathlib import Path
try:
    from pyvda import VirtualDesktop, get_virtual_desktops
except ImportError:
    print("Error: pyvda library not found. Install with: pip install pyvda")
    sys.exit(1)

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
    Validates the image path before attempting to set it.
    """
    if not image_path:
        return "[!] No wallpaper defined for this desktop."
    
    # Validate file exists
    if not os.path.exists(image_path):
        return f"[!] File not found: {image_path}"
    
    # Validate file extension
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    file_ext = Path(image_path).suffix.lower()
    if file_ext not in valid_extensions:
        return f"[!] Invalid image format: {file_ext}. Use JPG, PNG, BMP, or GIF."
    
    # Convert to absolute path
    abs_path = os.path.abspath(image_path)
    
    try:
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
        )
        if not result:
            return f"[!] Failed to update wallpaper (API error): {abs_path}"
        return f"[+] Wallpaper updated to: {os.path.basename(abs_path)}"
    except Exception as e:
        return f"[!] Error setting wallpaper: {str(e)}"

def curses_input(stdscr, prompt, y, x):
    """
    Prompt the user for input in curses with error handling.
    """
    try:
        max_y, max_x = stdscr.getmaxyx()
        # Ensure we're within bounds
        if y >= max_y - 1 or x >= max_x - 1:
            return ""
        
        curses.echo()
        stdscr.addstr(y, x, prompt[:max_x - x - 1])
        stdscr.refresh()
        # Read up to 60 characters or remaining space
        max_input = min(60, max_x - x - len(prompt) - 1)
        input_str = stdscr.getstr(y, x + len(prompt), max_input).decode("utf-8", errors="replace")
        curses.noecho()
        return input_str.strip()
    except Exception as e:
        curses.noecho()
        return ""

def safe_addstr(stdscr, y, x, text, max_y=None, max_x=None):
    """
    Safely add string to screen with bounds checking.
    """
    try:
        if max_y is None or max_x is None:
            max_y, max_x = stdscr.getmaxyx()
        
        if y < max_y - 1 and x < max_x - 1:
            # Truncate text to fit within bounds
            available_space = max_x - x - 1
            text = text[:available_space]
            stdscr.addstr(y, x, text)
            return True
    except curses.error:
        pass
    return False

def main_curses(stdscr):
    global enabled, wallpapers

    curses.curs_set(0)      # Hide the cursor.
    stdscr.nodelay(True)    # Non-blocking input.
    stdscr.timeout(500)     # Refresh every 500 ms.

    current_desktop = None
    last_message = ""
    message_time = 0

    while True:
        try:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()

            # Check minimum terminal size
            if max_y < 20 or max_x < 80:
                safe_addstr(stdscr, 0, 0, "Terminal too small! Minimum 80x20 required.", max_y, max_x)
                stdscr.refresh()
                time.sleep(0.5)
                continue

            # Print the ASCII banner at the top
            banner_lines = ASCII_BANNER.split('\n')
            for i, line in enumerate(banner_lines):
                if i < max_y - 1:
                    safe_addstr(stdscr, i, 0, line, max_y, max_x)

            row_offset = len(banner_lines) + 1
            if row_offset >= max_y - 10:
                row_offset = 2  # Fallback if terminal is small

            safe_addstr(stdscr, row_offset, 0, "[q] Quit  |  [p] Toggle Enabled/Disabled  |  [c] Change Wallpaper", max_y, max_x)
            safe_addstr(stdscr, row_offset + 1, 0, "[a] Add Mapping | [d] Delete Mapping | [v] Validate Paths", max_y, max_x)

            # Show current status
            status_line = f"Wallpaper auto-update is: {'ENABLED' if enabled else 'DISABLED'}"
            safe_addstr(stdscr, row_offset + 3, 0, status_line, max_y, max_x)

            # Show current mappings
            safe_addstr(stdscr, row_offset + 5, 0, "Current Wallpaper Mappings:", max_y, max_x)
            line = row_offset + 6
            for d_num, w_path in sorted(wallpapers.items()):
                display_path = w_path or '(no wallpaper)'
                # Truncate long paths
                if len(display_path) > max_x - 20:
                    display_path = "..." + display_path[-(max_x - 23):]
                safe_addstr(stdscr, line, 2, f"Desktop {d_num}: {display_path}", max_y, max_x)
                line += 1
                if line >= max_y - 8:  # Leave room for other info
                    safe_addstr(stdscr, line, 2, "... (more)", max_y, max_x)
                    line += 1
                    break

            # Attempt to detect the current desktop and update wallpaper if enabled.
            try:
                desktop = VirtualDesktop.current()
                idx = desktop.number
                safe_addstr(stdscr, line + 1, 0, f"[-] Current Virtual Desktop: {idx}", max_y, max_x)
                
                # Auto-update wallpaper if there's a change in desktop and it's enabled.
                if enabled and (idx != current_desktop):
                    current_desktop = idx
                    wallpaper_path = wallpapers.get(idx, "")
                    result_msg = set_wallpaper(wallpaper_path)
                    last_message = result_msg
                    message_time = time.time()
                    safe_addstr(stdscr, line + 2, 0, result_msg, max_y, max_x)
                elif last_message and (time.time() - message_time < 5):
                    # Show last message for 5 seconds
                    safe_addstr(stdscr, line + 2, 0, last_message, max_y, max_x)
                    
            except AttributeError as e:
                error_msg = "[Error] Could not get desktop number. Ensure you have virtual desktops."
                safe_addstr(stdscr, line + 3, 0, error_msg, max_y, max_x)
            except Exception as e:
                error_msg = f"[Error] {str(e)[:max_x - 20]}"
                safe_addstr(stdscr, line + 3, 0, error_msg, max_y, max_x)

            # Show helpful info
            safe_addstr(stdscr, line + 5, 0, "[-] Monitoring virtual desktop changes...", max_y, max_x)

            stdscr.refresh()

            # Grab user input
            key = stdscr.getch()

            if key == ord('q'):
                break  # Quit
            elif key == ord('p'):
                enabled = not enabled
                last_message = f"[*] Auto-update {'ENABLED' if enabled else 'DISABLED'}"
                message_time = time.time()
            elif key == ord('v'):
                # Validate all wallpaper paths
                stdscr.nodelay(False)
                safe_addstr(stdscr, line + 7, 0, "Validating wallpaper paths...", max_y, max_x)
                stdscr.refresh()
                validation_line = line + 8
                for desk_idx, path in sorted(wallpapers.items()):
                    if path:
                        if os.path.exists(path):
                            safe_addstr(stdscr, validation_line, 0, f"[+] Desktop {desk_idx}: OK", max_y, max_x)
                        else:
                            safe_addstr(stdscr, validation_line, 0, f"[!] Desktop {desk_idx}: FILE NOT FOUND", max_y, max_x)
                    else:
                        safe_addstr(stdscr, validation_line, 0, f"[-] Desktop {desk_idx}: No wallpaper set", max_y, max_x)
                    validation_line += 1
                    if validation_line >= max_y - 2:
                        break
                safe_addstr(stdscr, validation_line + 1, 0, "Press any key to continue...", max_y, max_x)
                stdscr.refresh()
                stdscr.getch()
                stdscr.nodelay(True)
            elif key == ord('c'):
                # Change wallpaper for a specific desktop
                stdscr.nodelay(False)
                idx_str = curses_input(stdscr, "Enter desktop number to change: ", line + 7, 0)
                if not idx_str:
                    stdscr.nodelay(True)
                    continue
                try:
                    desk_idx = int(idx_str)
                except ValueError:
                    safe_addstr(stdscr, line + 8, 0, "[!] Invalid number. Press any key.", max_y, max_x)
                    stdscr.getch()
                    stdscr.nodelay(True)
                    continue
                path = curses_input(stdscr, "Enter new wallpaper path: ", line + 9, 0)
                if path:
                    wallpapers[desk_idx] = path
                    last_message = f"[+] Desktop {desk_idx} wallpaper changed"
                    message_time = time.time()
                    safe_addstr(stdscr, line + 10, 0, last_message, max_y, max_x)
                stdscr.getch()
                stdscr.nodelay(True)
            elif key == ord('a'):
                # Add a new mapping
                stdscr.nodelay(False)
                idx_str = curses_input(stdscr, "Enter new desktop number: ", line + 7, 0)
                if not idx_str:
                    stdscr.nodelay(True)
                    continue
                try:
                    desk_idx = int(idx_str)
                except ValueError:
                    safe_addstr(stdscr, line + 8, 0, "[!] Invalid number. Press any key.", max_y, max_x)
                    stdscr.getch()
                    stdscr.nodelay(True)
                    continue
                if desk_idx in wallpapers:
                    safe_addstr(stdscr, line + 8, 0, "[!] Mapping exists. Use 'Change' instead. Press any key.", max_y, max_x)
                    stdscr.getch()
                    stdscr.nodelay(True)
                    continue
                path = curses_input(stdscr, "Enter new wallpaper path: ", line + 9, 0)
                wallpapers[desk_idx] = path
                last_message = f"[+] Added: Desktop {desk_idx}"
                message_time = time.time()
                safe_addstr(stdscr, line + 10, 0, last_message, max_y, max_x)
                stdscr.getch()
                stdscr.nodelay(True)
            elif key == ord('d'):
                # Delete a mapping
                stdscr.nodelay(False)
                idx_str = curses_input(stdscr, "Enter desktop number to delete: ", line + 7, 0)
                if not idx_str:
                    stdscr.nodelay(True)
                    continue
                try:
                    desk_idx = int(idx_str)
                except ValueError:
                    safe_addstr(stdscr, line + 8, 0, "[!] Invalid number. Press any key.", max_y, max_x)
                    stdscr.getch()
                    stdscr.nodelay(True)
                    continue
                if desk_idx in wallpapers:
                    del wallpapers[desk_idx]
                    last_message = f"[+] Deleted mapping for desktop {desk_idx}"
                    message_time = time.time()
                    safe_addstr(stdscr, line + 8, 0, last_message, max_y, max_x)
                else:
                    safe_addstr(stdscr, line + 8, 0, f"[!] No mapping found for desktop {desk_idx}", max_y, max_x)
                stdscr.getch()
                stdscr.nodelay(True)

            time.sleep(0.1)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            # Catch any unexpected errors to prevent crash
            try:
                safe_addstr(stdscr, 0, 0, f"Unexpected error: {str(e)[:60]}", max_y, max_x)
                stdscr.refresh()
                time.sleep(2)
            except:
                break

if __name__ == "__main__":
    try:
        # Validate at least one wallpaper mapping exists
        if not wallpapers:
            print("[!] Warning: No wallpaper mappings defined in the configuration.")
            print("[!] Edit the 'wallpapers' dictionary in vdw.py to add mappings.")
        
        # Check if running on Windows
        if sys.platform != "win32":
            print("[!] Error: This application only works on Windows.")
            sys.exit(1)
        
        # Try to import windows-curses
        try:
            import curses
        except ImportError:
            print("[!] Error: windows-curses not installed.")
            print("[!] Install with: pip install windows-curses")
            sys.exit(1)
        
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        print("\n[*] Application closed by user.")
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        print("[!] Make sure you have:")
        print("    1. Installed pyvda: pip install pyvda")
        print("    2. Installed windows-curses: pip install windows-curses")
        print("    3. Created at least 2 virtual desktops in Windows")
        sys.exit(1)
