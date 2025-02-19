# External Libs.
import platform
import pyautogui
from pynput.keyboard import Controller
import time
import os
import threading
from pathlib import Path
from threading import Event
from rich.console import Console
from elevenlabs.client import ElevenLabs
import subprocess
from typing import Literal
from contextlib import contextmanager

# Internal Libs.
from ._infrastructure._audio import AudioManager
from ._infrastructure._video import VideoManager
from ._infrastructure._ai import PromptManager, GoogleGenAI
from ._utils import (
    parse_code,
    _is_jupyter_idle,
    _get_audio_length,
)
from ._platforms import PlatformManager
from .scene import CodingScene

_console = Console()


class TimingConfig:
    """Configuration for various timing constants used in the tutorial creation."""

    JUPYTER_STARTUP_DELAY = 6.0
    CHAR_TYPE_DELAY = 0.1
    IDLE_CHECK_INTERVAL = 0.5
    POST_CELL_PADDING = 10.0
    EXECUTION_TIMEOUT = 60.0  # Move timeout duration here
    RECORDING_FPS = 20  # Move FPS value here


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
        path_info: str | Path,
        narration_type: Literal["after", "parallel"] = "after",
        language: str = "python3",
        force_approve: bool = False,
    ) -> None:
        """Initialize the CodingTutorial class.

        Args:
            topic: The tutorial topic
            eleven_labs_api_key: API key for ElevenLabs voice synthesis
            eleven_labs_voice_id: Voice ID for ElevenLabs synthesis
            model_object: AI model for code generation
            path_info: Path information for file operations
            narration_type: When to play narration ('after' or 'parallel')
            language: Programming language for the tutorial
            force_approve: Whether to skip manual approval steps

        Raises:
            ValueError: If invalid parameters are provided
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")

        if not eleven_labs_api_key:
            raise ValueError("ElevenLabs API key is required")

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
        self.path_info = path_info
        self.narration_type = narration_type
        self.language = language
        self.force_approve = force_approve

        self._prompt_manager = PromptManager(language=self.language, topic=self.topic)
        self._platform_manager = PlatformManager(platform.system(), self.language)

        self.time_dict = {}

        self.matplotlib_event = Event()
        self.video_manager = VideoManager(self._platform_manager)
        self.audio_manager = AudioManager(
            self._client,
            self._prompt_manager,
            self.model_object,
            self.voice_object,
            force_approve,
        )

        assert path_info is not None

    def _generate_tutorial_code(self) -> list[str]:
        """Generates tutorial code snippets using the AI model."""
        try:
            _prompt = self._prompt_manager.build_prompt()
            _response = self.model_object.generate_tutorial_code(_prompt)
            _code = parse_code(_response)
            if not _code:
                raise ValueError("No code snippets were generated")
            return _code
        except Exception as e:
            _console.log(f"[red]Error generating tutorial code: {str(e)}")
            raise

    def _get_jupyter_window_id(self):
        """Retrieves the window ID of the active Jupyter console."""
        return self._platform_manager.get_window_id()

    def _get_window_coordinates_by_id(self, window_id: str):
        """Gets the screen coordinates of a window given its ID."""
        return self._platform_manager.get_coordinates_using_id(window_id)

    def _start_background_threads(self, window_id: str):
        """Initializes and starts recording and matplotlib monitoring threads."""
        recording_thread = threading.Thread(
            target=self.video_manager.record_window,
            args=(window_id, Path("pycoding_data/screen_recording.mp4"), 20),
            daemon=True,  # Make thread daemon
        )
        recording_thread.start()

        matplotlib_thread = threading.Thread(
            target=self._platform_manager.detect_and_close_matplotlib_window,
            args=(self.matplotlib_event,),
            daemon=True,  # Make thread daemon
        )
        matplotlib_thread.start()
        return recording_thread, matplotlib_thread

    def _join_threads(
        self, recording_thread: threading.Thread, matplotlib_thread: threading.Thread
    ):
        """Waits for background threads to complete execution."""
        # Wait for threads with timeout
        recording_thread.join(timeout=5)
        matplotlib_thread.join(timeout=5)

        # Log warning if threads didn't complete
        if recording_thread.is_alive():
            _console.log(
                "[yellow]Warning: Recording thread did not exit cleanly[/yellow]"
            )
        if matplotlib_thread.is_alive():
            _console.log(
                "[yellow]Warning: Matplotlib thread did not exit cleanly[/yellow]"
            )

    def _type_code(
        self, code_cells: list[str], keyboard: Controller, proc: subprocess.Popen
    ) -> dict[str, dict[str, float]]:
        """Types and executes code cells while managing timing and audio synchronization."""
        time_dict = {}
        prev_end_time = time.time()

        for i, cell in enumerate(code_cells):
            _start = prev_end_time
            time_dict[str(i)] = {
                "Start": _start,
                "End": None,
                "Audio-Start": None,
            }

            _splitted_cell = cell.splitlines()

            # Track the start of actual code execution
            execution_start = time.time()

            _cell = CodingScene(
                _splitted_cell, self.language, TimingConfig.CHAR_TYPE_DELAY
            )
            _cell.type_code()

            pyautogui.hotkey("alt", "enter")

            # Wait for execution with timeout
            timeout_start = time.time()
            timeout_duration = 60  # 1 minute timeout
            while not _is_jupyter_idle(proc):
                if time.time() - timeout_start > timeout_duration:
                    _console.log(f"Warning: Cell {i} execution timed out")
                    break
                time.sleep(TimingConfig.IDLE_CHECK_INTERVAL)

            if not self.matplotlib_event.is_set():
                self.matplotlib_event.clear()

            _end = time.time()
            code_exec_time = _end - execution_start

            __cur_audio_path = self.audio_path / f"snippet_{i}.mp3"
            self.audio_manager._generate_single_audio(cell, __cur_audio_path)
            _audio_length = _get_audio_length(__cur_audio_path)

            if self.narration_type == "parallel":
                audio_start = _start
                # Use max to ensure we don't cut off either code or audio
                final_end = (
                    _start
                    + max(code_exec_time, _audio_length)
                    + TimingConfig.POST_CELL_PADDING
                )
                padding_time = final_end - (_start + code_exec_time)
                if padding_time > 0:
                    time.sleep(padding_time)

            else:
                audio_start = _end
                final_end = _end + _audio_length + TimingConfig.POST_CELL_PADDING

            time_dict[str(i)]["Audio-Start"] = audio_start
            time_dict[str(i)]["End"] = final_end

            prev_end_time = final_end

        return time_dict

    @contextmanager
    def _recording_session(self):
        """Context manager for handling recording session setup and cleanup."""
        keyboard = Controller()
        proc = self._platform_manager.open_jupyter_console()
        time.sleep(TimingConfig.JUPYTER_STARTUP_DELAY)

        window_id = self._get_jupyter_window_id()
        recording_thread, matplotlib_thread = self._start_background_threads(window_id)

        try:
            yield keyboard, proc
        finally:
            # Signal threads to stop
            self.video_manager.stop_recording()
            self.matplotlib_event.set()  # Signal matplotlib thread to stop
            self._join_threads(recording_thread, matplotlib_thread)

            # Force kill process if still running
            if proc and proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)

            # Close window as final cleanup
            if window_id:
                self._platform_manager.close_window_by_id(window_id)

    def _main(self):
        """Orchestrates the main tutorial creation workflow."""
        code_cells = self._generate_tutorial_code()
        with self._recording_session() as (keyboard, proc):
            self.time_dict = self._type_code(code_cells, keyboard, proc)
        self.video_manager.overlay_audio(self.time_dict, self.audio_path)

    def make_tutorial(self):
        """Creates a complete tutorial by executing the main workflow."""
        self._main()
