import subprocess
import time
from rich.console import Console
import pygetwindow as gw

_console = Console()


class WindowsManager:
    def __init__(self, language):
        self.language = language
        self.unique_title = f"JupyterConsole"
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
        """
        Launch a new Command Prompt window that runs:
          jupyter console --kernel <language>
        We use the 'start' command to open a new window. Note that this
        requires the jupyter executable to be in your PATH.
        """
        try:
            # The /k switch tells cmd.exe to run the command and then remain open.
            # Using shell=True because 'start' is a shell builtin.
            command = (
                f"title {self.unique_title} && jupyter console --kernel {self.language}"
            )

            proc = subprocess.Popen(
                ["cmd", "/k", command],  # '/k' keeps the console open
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            time.sleep(1)
            return proc

        except Exception as e:
            _console.log(f"[red]Error launching Jupyter console: {e}[/red]")
            return None
