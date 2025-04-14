import os
import time
import threading
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from pyvda import VirtualDesktop

# Constants for the Windows API call
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02

class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Desktop Wallpaper Switcher")
        self.root.geometry("450x300")
        self.wallpapers = {1: "", 2: ""}
        self.monitoring_thread = None
        self.monitoring = False
        self.current_desktop = None

        # Create the GUI components
        self.create_widgets()

    def create_widgets(self):
        # Frame for Desktop 1 Wallpaper
        frame1 = tk.Frame(self.root, pady=10)
        frame1.pack(fill="x")
        tk.Label(frame1, text="Desktop 1 Wallpaper:").pack(side="left", padx=5)
        self.wp1_entry = tk.Entry(frame1, width=40)
        self.wp1_entry.pack(side="left", padx=5)
        tk.Button(frame1, text="Browse", command=lambda: self.select_file(1)).pack(side="left", padx=5)

        # Frame for Desktop 2 Wallpaper
        frame2 = tk.Frame(self.root, pady=10)
        frame2.pack(fill="x")
        tk.Label(frame2, text="Desktop 2 Wallpaper:").pack(side="left", padx=5)
        self.wp2_entry = tk.Entry(frame2, width=40)
        self.wp2_entry.pack(side="left", padx=5)
        tk.Button(frame2, text="Browse", command=lambda: self.select_file(2)).pack(side="left", padx=5)

        # Start/Stop buttons
        self.start_button = tk.Button(self.root, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop Monitoring", command=self.stop_monitoring, state="disabled")
        self.stop_button.pack()

        # Label to display current virtual desktop
        self.status_label = tk.Label(self.root, text="Current Virtual Desktop: N/A")
        self.status_label.pack(pady=20)

    def select_file(self, desktop):
        file_path = filedialog.askopenfilename(
            title="Select Wallpaper",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.wallpapers[desktop] = file_path
            if desktop == 1:
                self.wp1_entry.delete(0, tk.END)
                self.wp1_entry.insert(0, file_path)
            elif desktop == 2:
                self.wp2_entry.delete(0, tk.END)
                self.wp2_entry.insert(0, file_path)

    def set_wallpaper(self, image_path):
        """Set the desktop wallpaper using the Windows API."""
        if image_path and os.path.exists(image_path):
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, image_path,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
            if not result:
                print("Failed to update wallpaper:", image_path)
        else:
            print("Invalid image path provided:", image_path)

    def monitor_desktops(self):
        """Background thread that checks for virtual desktop switches and updates wallpaper accordingly."""
        while self.monitoring:
            try:
                desktop = VirtualDesktop.current()
                # pyvda uses desktop numbering starting at 1.
                index = desktop.number

                # Update the status label (use thread-safe method)
                self.root.after(0, lambda idx=index: self.status_label.config(text=f"Current Virtual Desktop: {idx}"))

                # Change wallpaper if desktop has changed
                if index != self.current_desktop:
                    self.current_desktop = index
                    print(f"Switched to virtual desktop {index}")
                    wp = self.wallpapers.get(index, "")
                    if wp:
                        self.set_wallpaper(wp)
                    else:
                        print("No wallpaper assigned for desktop", index)
            except Exception as e:
                print("Error:", e)
            time.sleep(1)

    def start_monitoring(self):
        # Update wallpaper mapping from the entry boxes.
        self.wallpapers[1] = self.wp1_entry.get().strip()
        self.wallpapers[2] = self.wp2_entry.get().strip()

        # Check if at least one wallpaper is set.
        if not self.wallpapers[1] and not self.wallpapers[2]:
            messagebox.showwarning("Missing Wallpapers", "Please select at least one wallpaper.")
            return

        self.monitoring = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.monitoring_thread = threading.Thread(target=self.monitor_desktops, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Monitoring stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WallpaperApp(root)
    root.mainloop()