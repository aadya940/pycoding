from ._linux import LinuxManager
from ._windows import WindowsManager


class PlatformManager:
    def __init__(self, platform, language):
        if platform == "Linux":
            self._platform = LinuxManager(language=language)
        elif platform == "Windows":
            self._platform = WindowsManager(language=language)

    def get_window_id(self):
        return self._platform.get_window_id()

    def get_coordinates_using_id(self, window_id):
        return self._platform.get_coordinates_using_id(window_id=window_id)

    def open_jupyter_console(self):
        return self._platform.open_jupyter_console()
