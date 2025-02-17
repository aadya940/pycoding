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

from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

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
        """Get the coordinates of a window by its ID using xwininfo."""
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

        matplotlib_thread = threading.Thread(
            target=self._platform_manager.detect_and_close_matplotlib_window,
        )
        matplotlib_thread.start()

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
                _audio_length = _get_audio_length(audio_files[i])
                if self.narration_type == "parallel":
                    audio_start = _start
                    final_end = _start + max(code_exec_time, _audio_length) + 10
                    __diff = final_end - (_start + code_exec_time)
                    if __diff > 0:
                        time.sleep(__diff)
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
            matplotlib_thread.join()

            subprocess.run(["wmctrl", "-i", "-c", window_id], check=True)

            self._overlay_audio_on_video()

    def _generate_audio_file(self, code_cells: list):
        """Generate individual audio files for each code snippet."""

        def _generate_audio_per_snippet(code_snippet: str, path: str):
            """Generate audio for one snippet and save it."""
            _prompt = f"""You are a coding tutor creating a voice narration script. Explain the following code snippet in a 
            conversational, easy-to-follow way that works well for text-to-speech narration.

            Code to explain:
            ```
            {code_snippet}
            ```

            Guidelines for your explanation:
            1. Start with a brief overview of what the code accomplishes
            2. Break down the explanation into short, clear sentences
            3. Avoid technical jargon unless necessary, and when used, briefly explain it
            4. Use natural speech patterns (e.g., "Let's look at...", "Notice how...", "This part is important because...")
            5. Keep sentences under 20 words for better TTS flow
            6. Include pauses by using periods and commas strategically
            7. Avoid special characters or symbols that might confuse TTS
            8. Use concrete examples or analogies where helpful
            9. End with a brief summary or key takeaway
            10. Don't use any type of Quotes or Markdown formatting. Also, ignore unnecessary explanations
            like `print` statements, `comments` etc.
            11. Refer to variable names or special characters by their names. For example, `_` as `underscore`,
            `is_variable` as `is underscore variable`.

            Format your response as a natural, flowing explanation
            """
            while True:
                try:
                    # Start a timer for the response
                    start_time = time.time()
                    _response = None

                    while time.time() - start_time < 25:  # 25 second timeout
                        try:
                            _response = self.model_object.send_message(_prompt)
                            break
                        except Exception as e:
                            if time.time() - start_time >= 25:
                                raise TimeoutError("Response timeout")
                            time.sleep(1)  # Wait before retry
                            continue

                    if _response is None:
                        raise TimeoutError("Response timeout")

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

                except TimeoutError:
                    _console.log("[yellow]Response timed out, retrying...[/yellow]")
                    continue

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
        self._platform_manager.make_fullscreen(window_id)
        time.sleep(2)
        coords = self._get_window_coordinates_by_id(window_id)
        if not coords:
            _console.log("[red]Error: Could not determine window coordinates.[/red]")
            return

        x, y, width, height = coords

        # Adjust region slightly to avoid UI glitches
        x += 2
        y += 2
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
        Handles timing synchronization between video and audio clips.
        """
        video_path = Path("pycoding_data/screen_recording.mp4")
        output_path = Path("pycoding_data/final_tutorial.mp4")
        temp_clips = []

        if not video_path.exists():
            _console.log("[red]Error: Screen recording file not found![/red]")
            return

        video = VideoFileClip(str(video_path))

        # Create a list to store all clips with their audio
        final_clips = []

        for key in sorted(self.time_dict.keys(), key=int):
            timing = self.time_dict[key]
            audio_file = self.audio_path / f"snippet_{key}.mp3"

            if not audio_file.exists():
                _console.log(
                    f"[yellow]Warning: Missing narration file {audio_file}[/yellow]"
                )
                continue

            # Calculate relative timestamps
            start_time = timing["Start"] - self.time_dict["0"]["Start"]
            end_time = min(timing["End"] - self.time_dict["0"]["Start"], video.duration)

            # Safety check for timestamps
            if start_time >= video.duration:
                _console.log(
                    f"[yellow]Warning: Clip {key} start time exceeds video duration[/yellow]"
                )
                continue

            # Extract video segment
            try:
                video_segment = video.subclipped(start_time, end_time)
            except Exception as e:
                _console.log(f"[red]Error processing clip {key}: {e}[/red]")
                continue

            # Add audio
            audio_clip = AudioFileClip(str(audio_file))

            # If narration is longer than video segment, extend video segment duration
            if audio_clip.duration > video_segment.duration:
                # Freeze last frame for remaining audio duration
                video_segment = video_segment.with_duration(audio_clip.duration)

            # Combine video and audio
            final_clips.append(video_segment.with_audio(audio_clip))

        # Concatenate all clips
        if final_clips:
            final_video = concatenate_videoclips(final_clips)

            # Write final video
            try:
                final_video.write_videofile(
                    str(output_path), codec="libx264", fps=video.fps, audio_codec="aac"
                )
            except Exception as e:
                _console.log(f"[red]Error writing final video: {e}[/red]")
            finally:
                final_video.close()

        # Clean up
        video.close()
        video_path.unlink(missing_ok=True)
        _console.log(f"[yellow]Deleted {video_path} after processing.[/yellow]")
        _console.log(f"[green]Final tutorial saved to {output_path}[/green]")

    def make_tutorial(self):
        """Typewrite, Synchronize sound, Screen Record."""
        self._main()
