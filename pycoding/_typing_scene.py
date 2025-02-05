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
import subprocess
import os
import threading
import shutil
from pathlib import Path

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from moviepy import VideoFileClip, AudioFileClip

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
        """
        Get the coordinates of a window by its ID using xwininfo.
        """
        # Use PlatformManager
        return self._platform_manager.get_coordinates_using_id(window_id)

    def _main(self):
        # Generate Code Cells.
        code_cells = self._generate_tutorial_code()
        audio_files = self._generate_audio_file(code_cells)
        keyboard = Controller()

        assert len(code_cells) == len(audio_files)

        # Open Jupyter shell.
        proc = self._platform_manager.open_jupyter_console()
        time.sleep(6)  # Give it time to load.

        window_id = self._get_jupyter_window_id()
        _console.log(f"Window ID for the Jupyter Console: {window_id}")

        self.recording_process = True

        # Start screen recording
        recording_thread = threading.Thread(
            target=self._record_window_by_id,
            args=(window_id, Path("pycoding_data/screen_recording.mp4"), 20),
        )
        recording_thread.start()

        try:
            prev_end_time = time.time()  # Track previous end time
            for i, cell in enumerate(code_cells):
                # Record start time
                _start = prev_end_time  # Start immediately after the previous segment
                self.time_dict[str(i)] = {
                    "Start": _start,
                    "End": None,
                    "Audio-Start": None,
                }

                # Typewrite the code
                for line in cell.splitlines():
                    for char in line:
                        keyboard.press(char)
                        time.sleep(0.1)
                        keyboard.release(char)
                    pyautogui.press("enter")  # Execute line

                # Wait for execution to finish
                while not _is_jupyter_idle(proc):
                    time.sleep(0.5)

                _end = time.time()  # Execution end time
                code_exec_time = _end - _start

                # Calculate audio start & end times
                _audio_length = _get_audio_length(audio_files[i])
                if self.narration_type == "parallel":
                    audio_start = _start
                    final_end = _start + max(code_exec_time, _audio_length) + 10
                else:  # Narration after execution
                    audio_start = _end
                    final_end = _end + _audio_length + 10

                self.time_dict[str(i)]["Audio-Start"] = audio_start
                self.time_dict[str(i)]["End"] = final_end  # Assign final_end as End

                prev_end_time = final_end  # Update for the next snippet

        finally:
            # End recording
            self._end_screen_recording()
            recording_thread.join()

            self._overlay_audio_on_video()

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

                if self.force_approve:
                    break

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

    def _record_window_by_id(self, window_id: str, output_filename: str, fps: int = 20):
        """Records a specific window region along with audio, supporting Windows, Linux, and macOS."""

        coords = self._get_window_coordinates_by_id(window_id)
        if not coords:
            _console.log("[red]Error: Could not determine window coordinates.[/red]")
            return

        x, y, width, height = coords

        # Adjust region slightly to avoid UI glitches
        x += 1
        y += 1
        width -= 2
        height -= 2

        system = platform.system()

        # Ensure FFmpeg is installed
        if not shutil.which("ffmpeg"):
            _console.log("[red]Error: FFmpeg is not installed or not in PATH.[/red]")
            return

        # Platform-Specific Configuration
        if system == "Linux":
            screen_grab = "x11grab"  # More modern alternative to x11grab
            display = os.getenv("DISPLAY", ":0")
            screen_input = f"{display}.0+{x},{y}"
            frame_rate_flag = "-r"

        elif system == "Windows":
            screen_grab = "gdigrab"
            screen_input = "desktop"
            frame_rate_flag = "-framerate"

        elif system == "Darwin":  # macOS
            screen_grab = "avfoundation"
            screen_input = "1"  # Default main screen
            frame_rate_flag = "-r"

        else:
            _console.log("[red]Error: Unsupported platform.[/red]")
            return

        # Build the FFmpeg command in correct order
        ffmpeg_command = [
            "ffmpeg",
            "-f",
            screen_grab,
            frame_rate_flag,
            str(fps),
            "-video_size",
            f"{width}x{height}",
            "-i",
            screen_input,
            "-c:v",
            "h264",
            "-preset",
            "ultrafast",
        ]

        if system == "Linux":
            ffmpeg_command.extend(["-c:v", "libx264"])
        else:
            ffmpeg_command.extend(
                [
                    "-c:v",
                    "mpeg4",  # Use MPEG-4 codec instead of x264
                    "-q:v",
                    "5",  # Set quality (lower is better, adjust as needed)
                ]
            )

        # Add audio recording if available

        # Windows-specific fixes
        if system == "Windows":
            ffmpeg_command.insert(5, "-offset_x")
            ffmpeg_command.insert(6, str(x))
            ffmpeg_command.insert(7, "-offset_y")
            ffmpeg_command.insert(8, str(y))

        ffmpeg_command.extend(["-fps_mode", "passthrough"])
        ffmpeg_command.extend(["-movflags", "+faststart"])
        ffmpeg_command.extend(["-y", str(output_filename)])

        _console.log(
            f"Executing FFmpeg command:\n[cyan]{' '.join(ffmpeg_command)}[/cyan]"
        )

        # Start recording
        try:
            self.ffmpeg_process = subprocess.Popen(ffmpeg_command)

        except Exception as e:
            _console.log(f"[red]Error: Failed to start recording: {e}[/red]")

    def _end_screen_recording(self):
        """End the screen recording."""
        self.recording_process = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()  # Gracefully stops ffmpeg.
            self.ffmpeg_process.wait()

    def _overlay_audio_on_video(self):
        """
        Overlays narration audio on the recorded screen video using MoviePy.

        - Extracts "Audio-Start" times from self.time_dict.
        - Ensures proper synchronization of narration with screen recording.
        - Deletes `screen_recording.mp4` after processing.
        - Outputs `final_tutorial.mp4`.
        """

        video_path = Path("pycoding_data/screen_recording.mp4")
        output_path = Path("pycoding_data/final_tutorial.mp4")

        if not video_path.exists():
            _console.log("[red]Error: Screen recording file not found![/red]")
            return

        video = VideoFileClip(str(video_path))

        for key, timing in self.time_dict.items():
            audio_file = self.audio_path / f"snippet_{key}.mp3"
            if not audio_file.exists():
                _console.log(
                    f"[yellow]Warning: Missing narration file {audio_file}[/yellow]"
                )
                continue

            # Extract the relevant portion of the video
            clip_start = timing["Start"] - self.time_dict["0"]["Start"]
            clip_end = timing["End"] - self.time_dict["0"]["Start"]

            video_clip = video.subclip(clip_start, clip_end)

            # Extract the corresponding audio
            audio_clip = AudioFileClip(str(audio_file)).subclip(0, video_clip.duration)

            # Add the audio to the video
            final_clip = video_clip.set_audio(audio_clip)

            # Export final video
            final_clip.write_videofile(str(output_path), codec="libx264", fps=video.fps)

        # Delete screen recording after successful processing
        video_path.unlink(missing_ok=True)
        _console.log(f"[yellow]Deleted {video_path} after processing.[/yellow]")

        _console.log(f"[green]Final tutorial saved to {output_path}[/green]")

    def make_tutorial(self):
        """Typewrite, Synchronize sound, Screen Record."""
        self._main()
