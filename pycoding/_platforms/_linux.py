import subprocess
from rich.console import Console

_console = Console()


class LinuxManager:
    def __init__(self, language):
        # Check if `wmctrl` and `xwininfo` and `pactl` are present or not.
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

    def open_jupyter_console(self):
        proc = subprocess.Popen(
            ["gnome-terminal", "--", "jupyter", "console", "--kernel", self.language],
        )
        return proc

    def get_audio_device(self):
        try:
            # Query available audio devices using pactl (PulseAudio control tool)
            result = subprocess.run(
                ["pactl", "list", "short", "sources"],
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            output = result.stdout

            # Search for a monitor source (usually used for screen recording)
            for line in output.splitlines():
                if "monitor" in line:
                    # Extract the device name (1st column)
                    return line.split()[1]

            # Fallback to a default device if no monitor is found
            _console.log("No monitor source found. Falling back to the default device.")
            return "default"

        except Exception as e:
            _console.log(f"Error detecting audio device: {e}")
            return None
