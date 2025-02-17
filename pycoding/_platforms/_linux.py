import subprocess
import time


class LinuxManager:
    def __init__(self, language):
        # TODO, Check if `wmctrl` and `xwininfo` are present or not.
        self.language = language

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

    def detect_and_close_matplotlib_window(self):
        """Detect if matplotlib window is open and return its window ID."""
        try:
            # Run wmctrl to get all windows
            result = subprocess.run(
                ["wmctrl", "-lp"], stdout=subprocess.PIPE, text=True, check=True
            )
            output = result.stdout

            # Search for the line containing 'Image Viewer'
            for line in output.splitlines():
                if "Image Viewer" in line:
                    # Extract the window ID (1st field in the output)
                    parts = line.split()
                    if len(parts) > 0:
                        window_id = parts[0]  # Window ID is in the 1st column
                        # Close the window after 10 seconds.
                        time.sleep(11)
                        subprocess.run(["wmctrl", "-i", "-c", window_id], check=True)
            time.sleep(1)

        except Exception as e:
            print(f"Error detecting matplotlib window: {e}")
            time.sleep(1)
