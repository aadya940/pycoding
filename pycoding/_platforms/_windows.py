import subprocess
from rich.console import Console
import pygetwindow as gw
import sounddevice as sd
import platform

_console = Console()


class WindowsManager:
    def __init__(self, language):
        self.language = language
        self.unique_title = f"JupyterConsole_{self.language}"
        self._target_window = None

    def get_window_id(self):
        """Retrieve the window handle (hWnd) of the Jupyter console."""
        try:
            windows = gw.getWindowsWithTitle(self.unique_title)
            if windows:
                self._target_window = windows[0]
                return self._target_window._hWnd
            _console.log(f"No window found with title: {self.unique_title}")
        except Exception as e:
            _console.log(f"[bold red]Window detection error:[/bold red] {e}")
        return None

    def get_coordinates_using_id(self, window_id):
        """Fetch coordinates (left, top, width, height) of the window."""
        try:
            if not self._target_window or self._target_window._hWnd != window_id:
                self._target_window = next(
                    (w for w in gw.getAllWindows() if w._hWnd == window_id), None
                )

            if self._target_window:
                return (
                    self._target_window.left,
                    self._target_window.top,
                    self._target_window.width,
                    self._target_window.height,
                )

            _console.log(f"Window with ID {window_id} not found.")

        except Exception as e:
            _console.log(f"[bold red]Coordinate error:[/bold red] {e}")

        return None

    def open_jupyter_console(self):
        """Launch Jupyter console in a new command window with a unique title."""
        if platform.system() != "Windows":
            _console.log(
                "[bold yellow]This function is only supported on Windows.[/bold yellow]"
            )
            return None

        command = (
            f"title {self.unique_title} && jupyter console --kernel {self.language}"
        )

        try:
            proc = subprocess.Popen(
                ["cmd", "/k", command],  # '/k' keeps the console open
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return proc

        except Exception as e:
            _console.log(f"[bold red]Jupyter console launch error:[/bold red] {e}")
            return None

    def get_audio_device(self):
        """Finds a loopback audio device for recording; defaults to the first available input device."""
        try:
            devices = sd.query_devices()
            loopback_device = next(
                (
                    dev["name"]
                    for dev in devices
                    if dev["max_input_channels"] > 0
                    and (
                        "loopback" in dev["name"].lower()
                        or "stereo mix" in dev["name"].lower()
                    )
                ),
                None,
            )

            if loopback_device:
                return loopback_device

            _console.log(
                "[bold yellow]No loopback device found. Using default input.[/bold yellow]"
            )
            return (
                sd.default.device["input"]
                if isinstance(sd.default.device, dict)
                else sd.default.device[0]
            )
        except Exception as e:
            _console.log(f"[bold red]Audio error:[/bold red] {e}")
            return None
