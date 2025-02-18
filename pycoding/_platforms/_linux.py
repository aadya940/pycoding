import subprocess
import time
from threading import Event
from dataclasses import dataclass


@dataclass
class Delays:
    """Configuration class for various delay values used in platform operations"""

    matplotlib_window_check: float = 1.0  # Delay between checks for matplotlib window
    matplotlib_window_close: float = 11.0  # Delay before closing matplotlib window


class LinuxManager:
    def __init__(self, language):
        # TODO, Check if `wmctrl` and `xwininfo` are present or not.
        self.language = language
        self.delays = Delays()

    def get_window_id(self):
        try:
            # Run wmctrl -lp and capture its output
            result = subprocess.run(
                ["wmctrl", "-lp"], stdout=subprocess.PIPE, text=True, check=True
            )
            output = result.stdout

            # Search for the line containing 'Terminal' (Where Jupyter is running)
            for line in output.splitlines():
                if "Terminal" in line:
                    # Extract the window ID (1st field in the output)
                    parts = line.split()

                    if len(parts) > 0:
                        return parts[0]  # Window ID is in the 1st column

            return None  # If no match was found

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_coordinates_using_id(self, window_id):
        assert window_id is not None

        try:
            # Use xwininfo to get details of the window by ID
            result = subprocess.run(
                ["xwininfo", "-id", str(window_id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                print(f"Error: {result.stderr.strip()}")
                return None

            # Parse xwininfo output
            output = result.stdout
            x = int(output.split("Absolute upper-left X:")[1].split()[0])
            y = int(output.split("Absolute upper-left Y:")[1].split()[0])
            width = int(output.split("Width:")[1].split()[0])
            height = int(output.split("Height:")[1].split()[0])

            return x, y, width, height

        except Exception as e:
            print(f"Error fetching window coordinates: {e}")
            return None

    def make_fullscreen(self, window_id):
        """Resizes the specified window to 1920x1080 (16:9) aspect ratio
        as needed by popular platforms like Udemy, YouTube etc."""
        try:
            # Execute wmctrl command to resize the window
            subprocess.run(
                ["wmctrl", "-i", "-r", window_id, "-b", "toggle,fullscreen"], check=True
            )
            print(f"Window {window_id} resized to 1920x1080 (16:9)")
        except subprocess.CalledProcessError as e:
            print(f"Error resizing window {window_id}: {e}")

    def open_jupyter_console(self):
        proc = subprocess.Popen(
            ["gnome-terminal", "--", "jupyter", "console", "--kernel", self.language],
        )
        return proc

    def detect_and_close_matplotlib_window(self, event):
        """Detect if matplotlib window is open and return its window ID."""
        try:
            # Run wmctrl to get all windows
            result = subprocess.run(
                ["wmctrl", "-lp"], stdout=subprocess.PIPE, text=True, check=True
            )
            output = result.stdout

            # Search for the line containing 'Image Viewer'
            window_found = False
            for line in output.splitlines():
                if "Image Viewer" in line:
                    window_found = True
                    # Extract the window ID (1st field in the output)
                    parts = line.split()
                    if len(parts) > 0:
                        window_id = parts[0]  # Window ID is in the 1st column
                        # Close the window after configured delay
                        time.sleep(self.delays.matplotlib_window_close)
                        self.close_window_by_id(window_id)

            # Set the event whether we found a window or not
            event.set()

            if not window_found:
                time.sleep(
                    self.delays.matplotlib_window_check
                )  # Brief pause before checking again
                self.detect_and_close_matplotlib_window(
                    event
                )  # Recursive call to keep checking

        except Exception as e:
            print(f"Error detecting matplotlib window: {e}")
            event.set()  # Ensure we don't block the main thread even if there's an error
            time.sleep(self.delays.matplotlib_window_check)

    def close_window_by_id(self, window_id: str):
        try:
            subprocess.run(["wmctrl", "-i", "-c", window_id], check=True)
        except Exception as e:
            print(f"Error closing window {window_id}: {e}")
