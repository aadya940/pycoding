from ._linux import LinuxManager


class PlatformManager:
    """Manage platform specific commands.
    Currently only supporting Linux and Windows.
    """

    def __init__(self, platform, language):
        if platform == "Linux":
            self._platform = LinuxManager(language=language)

    def get_window_id(self):
        return self._platform.get_window_id()

    def get_coordinates_using_id(self, window_id):
        return self._platform.get_coordinates_using_id(window_id=window_id)

    def open_jupyter_console(self):
        return self._platform.open_jupyter_console()

    def make_fullscreen(self, window_id):
        return self._platform.make_fullscreen(window_id=window_id)

    def close_window_by_id(self, window_id: str):
        return self._platform.close_window_by_id(window_id=window_id)

    def detect_and_close_matplotlib_window(self, event):
        return self._platform.detect_and_close_matplotlib_window(event=event)
