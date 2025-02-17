from ._ai import GoogleGenAI
from ._utils import (
    parse_code,
    _is_jupyter_idle,
    _get_audio_length,
)
from ._prompts import PromptManager
from ._platforms import PlatformManager

import platform
import pyautogui
from pynput.keyboard import Controller
import time
import os
import threading
from pathlib import Path

from elevenlabs.client import ElevenLabs

from rich.console import Console

from ._audio import AudioManager
from ._video import VideoManager

_console = Console()


class CodingTutorial:
    """
    Automates the creation of interactive coding tutorials with AI-generated explanations,
    screen recordings, and voice narration.

    Features:
    - Generates code snippets using an AI model.
    - Provides AI-generated explanations for each snippet.
    - Records the Jupyter terminal session while executing the code.
    - Uses ElevenLabs AI for natural-sounding voice narration.
    - Supports real-time narration (parallel) or post-execution narration (after).
    - Saves recorded tutorials with synchronized audio and screen capture.

    Attributes:
    -----------
    model_object : object
        AI model interface to generate code snippets and explanations.
    tutorial_topic : str
        The topic for which the tutorial is generated.
    narration_mode : str
        Mode of narration, either 'parallel' (while typing) or 'after' (post-execution).
    output_dir : str
        Directory where generated files (code, audio, video) are stored.
    narration_type : str
        Specify if narration happens during or after typewriting. (one of `after` or `parallel`)
        Defaults to `after`.
    language : str
        The name of your jupyter kernel, defaults to `python3`. Other languages are r, julia,
        rust, xcpp17 (for C++), bash.
    force_approve : boolean
        Approve LLM response by default or not. Defaults to False.
    """

    def __init__(
        self,
        topic: str,
        eleven_labs_api_key: str,
        eleven_labs_voice_id: str,
        model_object: GoogleGenAI,
        path_info=None,
        narration_type="after",
        language="python3",
        force_approve=False,
    ):
        self.topic = topic
        self.voice_object = {
            "API_KEY": eleven_labs_api_key,
            "voice_id": eleven_labs_voice_id,
        }
        self.model_object = model_object
        self.audio_path = None

        self.model_object.start_chat()
        os.environ["ELEVEN_API_KEY"] = self.voice_object["API_KEY"]

        self._client = ElevenLabs(
            api_key=eleven_labs_api_key,
        )

        os.makedirs(Path("pycoding_data/audio_files"), exist_ok=True)
        self.audio_path = Path("pycoding_data/audio_files")
        self.recording_process = None
        assert path_info is not None
        self.path_info = path_info
        self.narration_type = narration_type
        self.language = language
        self.force_approve = force_approve

        self._prompt_manager = PromptManager(language=self.language, topic=self.topic)
        self._platform_manager = PlatformManager(platform.system(), self.language)

        self.time_dict = {}

        self.video_manager = VideoManager(self._platform_manager)
        self.audio_manager = AudioManager(
            self._client,
            self._prompt_manager,
            self.model_object,
            self.voice_object,
            force_approve,
        )

    def _generate_tutorial_code(self):
        _prompt = self._prompt_manager.build_prompt()
        while True:
            _response = self.model_object.send_message(_prompt)
            _console.log(_response)

            if self.force_approve:
                break

            _approval = input(f"Do you approve the code snippets? (yes/no): ")

            if _approval.lower() == "yes":
                break

            else:
                _feedback = input("Provide feedback to improve the response: ")
                self.model_object.send_message(_feedback)

        _code = parse_code(_response)  # Must return a list of code snippets.
        return _code

    def _get_jupyter_window_id(self):
        # Use PlatformManager
        return self._platform_manager.get_window_id()

    def _get_window_coordinates_by_id(self, window_id: str):
        """Get the coordinates of a window by its ID using xwininfo."""
        # Use PlatformManager
        return self._platform_manager.get_coordinates_using_id(window_id)

    def _start_background_threads(self, window_id: str):
        recording_thread = threading.Thread(
            target=self.video_manager.record_window,
            args=(window_id, Path("pycoding_data/screen_recording.mp4"), 20),
        )
        recording_thread.start()

        matplotlib_thread = threading.Thread(
            target=self._platform_manager.detect_and_close_matplotlib_window,
        )
        matplotlib_thread.start()
        return recording_thread, matplotlib_thread

    def _join_threads(
        self, recording_thread: threading.Thread, matplotlib_thread: threading.Thread
    ):
        recording_thread.join()
        matplotlib_thread.join()

    def _type_code(self, code_cells, keyboard, proc):
        """Handle code typing and execution."""
        time_dict = {}
        prev_end_time = time.time()

        for i, cell in enumerate(code_cells):
            # Record start time
            _start = prev_end_time  # Start immediately after the previous segment
            time_dict[str(i)] = {
                "Start": _start,
                "End": None,
                "Audio-Start": None,
            }

            _splitted_cells = cell.splitlines()

            # Typewrite the code
            for idx in range(len(_splitted_cells)):  # FIXED: Use range(len())
                indent_gap = None

                line = _splitted_cells[idx]

                if "python" in self.language:
                    # Jupyter console automatically handles indentation.
                    stripped_line = line.lstrip()

                    next_line = (
                        _splitted_cells[idx + 1]
                        if (idx + 1) < len(_splitted_cells)
                        else None
                    )
                    curr_indent = len(line) - len(stripped_line)
                    if next_line is not None:
                        next_indent = len(next_line) - len(next_line.lstrip())
                        indent_gap = next_indent - curr_indent

                else:
                    stripped_line = line

                for char in stripped_line:
                    keyboard.press(char)
                    time.sleep(0.1)
                    keyboard.release(char)
                pyautogui.press("enter")  # Execute line

                if indent_gap is not None:
                    if indent_gap < 0:
                        for _ in range(-1 * indent_gap):
                            pyautogui.press("backspace")

            pyautogui.hotkey("alt", "enter")

            # Wait for execution to finish
            while not _is_jupyter_idle(proc):
                time.sleep(0.5)

            _end = time.time()  # Execution end time
            code_exec_time = _end - _start

            # Calculate audio start & end times
            _audio_length = _get_audio_length(
                self.audio_manager.generate_audio_files([cell], self.audio_path)[0]
            )
            if self.narration_type == "parallel":
                audio_start = _start
                final_end = _start + max(code_exec_time, _audio_length) + 10
                __diff = final_end - (_start + code_exec_time)
                if __diff > 0:
                    time.sleep(__diff)
            else:  # Narration after execution
                audio_start = _end
                final_end = _end + _audio_length + 10

            time_dict[str(i)]["Audio-Start"] = audio_start
            time_dict[str(i)]["End"] = final_end  # Assign final_end as End

            prev_end_time = final_end  # Update for the next snippet

        return time_dict

    def _main(self):
        # Generate code and audio
        code_cells = self._generate_tutorial_code()
        audio_files = self.audio_manager.generate_audio_files(
            code_cells, self.audio_path
        )

        # Setup and start recording
        keyboard = Controller()
        proc = self._platform_manager.open_jupyter_console()
        time.sleep(6)

        window_id = self._get_jupyter_window_id()
        recording_thread, matplotlib_thread = self._start_background_threads(window_id)

        try:
            # Execute code typing
            self.time_dict = self._type_code(code_cells, keyboard, proc)
        finally:
            # Cleanup
            self.video_manager.stop_recording()
            self._join_threads(recording_thread, matplotlib_thread)
            self._platform_manager.close_window_by_id(window_id)
            self.video_manager.overlay_audio(self.time_dict, self.audio_path)

    def make_tutorial(self):
        """Typewrite, Synchronize sound, Screen Record."""
        self._main()
