from ._linux import LinuxManager
from ._windows import WindowsManager


class PlatformManager:
    def __init__(self, platform):
        if platform == "Linux":
            self._platform = LinuxManager()
        elif platform == "Windows":
            self._platform = WindowsManager()

    def get_window_id(self):
        return self._platform.get_window_id()

    def get_coordinates_using_id(self):
        return self._platform.get_coordinates_using_id()

    def open_jupyter_console(self):
        return self._platform.open_jupyter_console()

    def get_audio_device(self):
        return self._platform.get_audio_device()
