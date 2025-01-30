from ._ai import GoogleGenAI
from ._utils import (
    parse_code,
    _play_audio_on_cell_execution,
    _is_jupyter_idle,
)
from ._prompts import PromptManager

import pyautogui
import time
import subprocess
import os
import threading
import nbformat

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

import ffmpeg
from rich.console import Console

_console = Console()


class CodingTutorial:
    """
    Automates the creation of interactive coding tutorials with AI-generated explanations,
    screen recordings, and voice narration.

    Features:
    - Generates Python code snippets using an AI model.
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
        The name of your jupyter kernel, defaults to `python3`.
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

        self._prompt_manager = PromptManager(self._language)

    def _generate_tutorial_code(self):
        _prompt = self._prompt_manager.build_prompt()
        while True:
            _response = self.model_object.send_message(_prompt)
            _console.log(_response)
            _approval = input(f"Do you approve the code snippets? (yes/no): ")

            if _approval.lower() == "yes":
                break

            else:
                _feedback = input("Provide feedback to improve the response: ")
                self.model_object.send_message(_feedback)

        _code = parse_code(_response)  # Must return a list of code snippets.
        return _code

    def _get_jupyter_window_id(self):
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

    def _get_window_coordinates_by_id(self, window_id: str):
        """
        Get the coordinates of a window by its ID using xwininfo.
        """
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

    def _main(self):
        # Generate Code Cells.
        code_cells = self._generate_tutorial_code()
        audio_files = self._generate_audio_file(code_cells)
        assert len(code_cells) == len(audio_files)

        # Open jupyter shell.
        proc = subprocess.Popen(
            ["gnome-terminal", "--", "jupyter", "console", "--kernel", self.language]
        )
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
                    self._audio_thread = threading.Thread(
                        target=_play_audio_on_cell_execution, args=(audio_files[i],)
                    )
                    self._audio_thread.start()

                for line in cell.splitlines():
                    pyautogui.typewrite(line, interval=0.1)  # Simulate typing the line.
                    pyautogui.press("enter")  # Press Enter to run the line.

                # Only start writing the next command after previous finishes execution.
                while not _is_jupyter_idle(proc):
                    time.sleep(0.5)

                if self.narration_type == "parallel":
                    self._audio_thread.join()

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
            """
            while True:
                _response = self.model_object.send_message(_prompt)
                _text = _response.strip()
                _console.log(_text)
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
        Detects the default audio device using PulseAudio or ALSA.
        Returns the device name if found, else None.
        """
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
