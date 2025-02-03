from ._ai import GoogleGenAI
from ._utils import (
    parse_code,
    _play_audio_on_cell_execution,
    _is_jupyter_idle,
    _get_audio_length,
)
from ._prompts import PromptManager
from ._platforms import PlatformManager
import platform

import pyautogui
from pynput.keyboard import Controller
import time
import subprocess
import os
import threading
import multiprocessing

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from rich.console import Console

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

        os.makedirs("pycoding_data/audio_files", exist_ok=True)
        self.audio_path = "pycoding_data/audio_files"
        self.recording_process = None
        assert path_info is not None
        self.path_info = path_info
        self.narration_type = narration_type
        self.language = language
        self.force_approve = force_approve

        self._prompt_manager = PromptManager(language=self.language, topic=self.topic)
        self._platform_manager = PlatformManager(platform.system(), self.language)

    def _generate_tutorial_code(self):
        _prompt = self._prompt_manager.build_prompt()
        while True:
            _response = self.model_object.send_message(_prompt)
            _console.log(_response)

            if not self.force_approve:
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
        """
        Get the coordinates of a window by its ID using xwininfo.
        """
        # Use PlatformManager
        return self._platform_manager.get_window_coordinates_using_id(window_id)

    def _main(self):
        # Generate Code Cells.
        code_cells = self._generate_tutorial_code()
        audio_files = self._generate_audio_file(code_cells)
        keyboard = Controller()

        assert len(code_cells) == len(audio_files)

        # Open jupyter shell.

        # Use PlatformManager
        proc = self._platform_manager.open_jupyter_console(self.language)
        time.sleep(6)  # Give it time to load.

        window_id = self._get_jupyter_window_id()
        _console.log(f"Window ID for the Jupyter Console: {window_id}")

        self.recording_process = True

        # No need to record the entire screen, we only need to know the window ID.
        # Start screen recording in a separate thread (recording based on the window ID).
        recording_thread = threading.Thread(
            target=self._record_window_by_id,
            args=(window_id, "pycoding_data/screen_recording.mp4", 20),
        )
        recording_thread.start()

        try:
            for i, cell in enumerate(code_cells):
                # Type the entire cell's code.
                if self.narration_type == "parallel":
                    self._audio_process = multiprocessing.Process(
                        target=_play_audio_on_cell_execution, args=(audio_files[i],)
                    )
                    self._audio_process.start()

                _in = time.time()

                for line in cell.splitlines():
                    for char in line:
                        keyboard.press(char)
                        time.sleep(0.1)
                        keyboard.release(char)

                    pyautogui.press("enter")  # Press Enter to run the line.

                # Only start writing the next command after previous finishes execution.
                while not _is_jupyter_idle(proc):
                    _console.log("In Jupyter Idle block.")
                    time.sleep(0.5)

                _out = time.time()
                _len = _out - _in

                _audio_length = _get_audio_length(audio_files[i])
                _diff = abs(_len - _audio_length)

                _console.log("Code Block came here.")

                if self.narration_type == "parallel":
                    self._audio_process.join(timeout=(_diff + 10))
                    if self._audio_process.is_alive():
                        _console.log(
                            "Audio process is taking too long. Terminating forcefully."
                        )
                        self._audio_process.terminate()

                # Play the corresponding audio file after each cell.
                if self.narration_type == "after":
                    _play_audio_on_cell_execution(audio_files[i])

        finally:
            # End the screen recording.
            self._end_screen_recording()
            recording_thread.join()

    def _generate_audio_file(self, code_cells: list):
        """Generate individual audio files for each code snippet."""

        def _generate_audio_per_snippet(code_snippet: str, path: str):
            """Generate audio for one snippet and save it."""
            _prompt = f"""Write a concise, line-by-line explanation for the following code snippet:

            {code_snippet}
            
            
            Ensure the explanation:
            1. Is no longer than 30 seconds when spoken.
            2. Uses simple English without reading the code directly.
            3. Focuses on describing what the code does in plain language, 
            as if explaining to someone unfamiliar with coding.
            4. Only include the response.
            5. Don't use short forms and don't address problematic words.
            (example: don't address `vec_add`, `vec_sub`, address
            `vec_1` as `vector 1` and so on ... Hope you get the point.)
            6. Address numbers with words, example `1` as `one`. Also address
            arrays with words, example [1, 2, 3] as `list with elements one, two
            and three.`
            7. Explain the philosophy behind different objects in the code.
            """
            while True:
                _response = self.model_object.send_message(_prompt)
                _text = _response.strip()
                _console.log(_text)

                if not self.force_approve:
                    _approve = input("Do you approve the explanation? (yes/no)")

                    if _approve == "yes":
                        break
                    else:
                        _feedback = input("What feedback do you have? ")
                        self.model_object.send_message(_feedback)

            # Generate audio for the response
            response = self._client.text_to_speech.convert(
                voice_id=self.voice_object["voice_id"],
                output_format="mp3_22050_32",
                text=_text,
                model_id="eleven_turbo_v2_5",
                voice_settings=VoiceSettings(
                    stability=0.1,
                    similarity_boost=1.0,
                    style=0.5,
                    use_speaker_boost=True,
                ),
            )

            # Save the audio in chunks
            with open(path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            _console.log(f"Audio file saved at {path}")

        audio_files = []
        for i, code_cell in enumerate(code_cells):
            audio_path = os.path.join(self.audio_path, f"snippet_{i}.mp3")
            _generate_audio_per_snippet(code_cell, audio_path)
            audio_files.append(audio_path)

        return audio_files

    def _get_default_audio_device(self):
        """
        Detects the default audio device using PulseAudio.
        Returns the device name if found, else None.
        """
        # Use PlatformManager
        return self._platform_manager.get_audio_device()

    def _record_window_by_id(self, window_id: str, output_filename: str, fps: int = 20):
        coords = self._get_window_coordinates_by_id(window_id)
        if not coords:
            return

        x, y, width, height = coords

        # Manually reduce dimensions
        x += 1  # Reduce x position by 1 (optional, adjust as needed)
        y += 1  # Reduce y position by 1 (optional, adjust as needed)
        width -= 2  # Reduce width by 2 units
        height -= 2  # Reduce height by 2 units

        monitor = {"top": y, "left": x, "width": width, "height": height}

        display = os.getenv("DISPLAY", ":0")  # Default to :0 if DISPLAY is not set
        audio_device = self._get_default_audio_device()

        # Define the ffmpeg command to capture both screen and audio
        ffmpeg_command = [
            "ffmpeg",
            "-f",
            "x11grab",  # Grab the screen using X11
            "-s",
            f"{width}x{height}",  # Set screen size
            "-i",
            f"{display}.0+{x},{y}",  # Capture the specific screen region
            "-f",
            "pulse",  # Capture audio from PulseAudio
            "-i",
            audio_device,  # Use the default audio input (adjust as necessary for your system)
            "-c:v",
            "libx264",  # Video codec
            "-r",
            str(fps),  # Frame rate
            "-c:a",
            "aac",  # Audio codec
            "-strict",
            "experimental",  # Allow experimental codecs
            "-y",  # Overwrite output file if it exists
            output_filename,  # Output video file
        ]

        # Force audio-video sync.
        ffmpeg_command.extend(["-async", "1", "-vsync", "1"])

        _console.log("Recording...")
        # Start recording using ffmpeg
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command)

    def _end_screen_recording(self):
        """End the screen recording."""
        self.recording_process = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()  # Gracefully stops ffmpeg
            self.ffmpeg_process.wait()

    def make_tutorial(self):
        """Typewrite, Synchronize sound, Screen Record."""
        self._main()
