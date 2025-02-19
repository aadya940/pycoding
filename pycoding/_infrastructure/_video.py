import platform
import time
import subprocess
import os
import shutil
from pathlib import Path
from rich.console import Console
from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
import concurrent.futures
from typing import List, Tuple
from .._utils import create_title
from pathlib import Path

_console = Console()


class VideoManager:
    """Manage Jupyter Console dimensions and ffmpeg for video."""

    def __init__(self, platform_manager):
        self.platform_manager = platform_manager
        self.ffmpeg_process = None
        self.recording_process = None
        self.fps = None

    def record_window(self, window_id: str, output_filename: str, fps: int = 20):
        """Records a specific window region."""
        self.platform_manager.make_fullscreen(window_id)
        time.sleep(2)
        coords = self.platform_manager.get_coordinates_using_id(window_id)
        if not coords:
            _console.log("[red]Error: Could not determine window coordinates.[/red]")
            return

        self.fps = fps  # Set fps

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

        else:
            _console.log("[red]Error: Unsupported platform.[/red]")
            return

        # Build the FFmpeg command in correct order
        ffmpeg_command = [
            "ffmpeg",
            "-f",
            screen_grab,
            frame_rate_flag,
            str(self.fps),
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
                    "mpeg4",
                    "-q:v",
                    "5",
                ]
            )

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

    def stop_recording(self):
        """End the screen recording."""
        self.recording_process = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()

    def _process_video_segment(self, params: Tuple, title) -> VideoFileClip:
        """Process a single video segment with its audio in parallel."""
        key, timing, video, audio_path, base_start = params

        if title is not None:
            try:
                _title_path = os.path.join(
                    str(Path("pycoding_data/title_files")),
                    title.replace(" ", "") + ".png",
                )
                _title_path = create_title(
                    title,
                    _title_path,
                    image_size=(
                        video.size[0],
                        video.size[1],
                    ),  # Use actual video dimensions
                )

                # Create the title clip
                image_clip = ImageClip(_title_path, duration=5)
                # No need to resize since it's already the correct size

            except Exception as e:
                _console.log(
                    f"[yellow]Warning: Failed to create title slide for segment {key}: {e}[/yellow]"
                )
                title = None

        audio_file = audio_path / f"snippet_{key}.mp3"
        if not audio_file.exists():
            _console.log(
                f"[yellow]Warning: Missing narration file {audio_file}[/yellow]"
            )
            return None

        # Calculate relative timestamps
        start_time = timing["Start"] - base_start
        end_time = min(timing["End"] - base_start, video.duration)

        # Safety check for timestamps
        if start_time >= video.duration:
            _console.log(
                f"[yellow]Warning: Clip {key} start time exceeds video duration[/yellow]"
            )
            return None

        try:
            video_segment = video.subclipped(start_time, end_time)
            audio_clip = AudioFileClip(str(audio_file))

            # If narration is longer than video segment, extend video segment duration
            if audio_clip.duration > video_segment.duration:
                video_segment = video_segment.with_duration(audio_clip.duration)

            # Combine video and audio
            if title is not None:
                return concatenate_videoclips(
                    [image_clip, video_segment.with_audio(audio_clip)],
                    method="compose",
                )

            return video_segment.with_audio(audio_clip)

        except Exception as e:
            _console.log(f"[red]Error processing clip {key}: {e}[/red]")
            return None

    def overlay_audio(self, time_dict, audio_path, titles=None):
        """Overlays narration audio on the recorded screen video."""
        video_path = Path("pycoding_data/screen_recording.mp4")
        output_path = Path("pycoding_data/final_tutorial.mp4")

        self.titles = titles

        if not video_path.exists():
            _console.log("[red]Error: Screen recording file not found![/red]")
            return

        video = VideoFileClip(str(video_path))
        base_start = time_dict["0"]["Start"]

        if self.titles is not None and len(self.titles) != len(time_dict):
            _console.log(
                f"[yellow]Warning: Number of titles ({len(self.titles)}) doesn't match number of code segments ({len(time_dict)})[/yellow]"
            )

        # Prepare parameters for parallel processing
        process_params = [
            (key, timing, video, audio_path, base_start)
            for key, timing in sorted(time_dict.items(), key=lambda x: int(x[0]))
        ]

        # Process video segments in parallel while maintaining order
        final_clips: List[VideoFileClip] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create all futures and store them with their indices
            futures_with_index = [
                (
                    i,
                    executor.submit(
                        self._process_video_segment,
                        params,
                        self.titles[i]
                        if self.titles and i < len(self.titles)
                        else None,
                    ),
                )
                for i, params in enumerate(process_params)
            ]

            # Wait for all futures to complete and process them in order
            for i, future in sorted(futures_with_index, key=lambda x: x[0]):
                result = future.result()
                if result is not None:
                    final_clips.append(result)

        # Concatenate all clips
        if final_clips:
            final_video = concatenate_videoclips(final_clips)

            # Write final video
            try:
                final_video.write_videofile(
                    str(output_path),
                    codec="libx264",
                    fps=video.fps,
                    audio_codec="aac",
                    threads=max(
                        1, os.cpu_count() - 1
                    ),  # Use multiple threads for encoding
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
