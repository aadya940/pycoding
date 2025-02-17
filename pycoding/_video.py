import platform
import time
import subprocess
import os
import shutil
from pathlib import Path
from rich.console import Console
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

_console = Console()


class VideoManager:
    def __init__(self, platform_manager):
        self.platform_manager = platform_manager
        self.ffmpeg_process = None
        self.recording_process = None

    def record_window(self, window_id: str, output_filename: str, fps: int = 20):
        """Records a specific window region."""
        self.platform_manager.make_fullscreen(window_id)
        time.sleep(2)
        coords = self.platform_manager.get_coordinates_using_id(window_id)
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

    def overlay_audio(self, time_dict, audio_path):
        """Overlays narration audio on the recorded screen video."""
        video_path = Path("pycoding_data/screen_recording.mp4")
        output_path = Path("pycoding_data/final_tutorial.mp4")

        if not video_path.exists():
            _console.log("[red]Error: Screen recording file not found![/red]")
            return

        video = VideoFileClip(str(video_path))

        # Create a list to store all clips with their audio
        final_clips = []

        for key in sorted(time_dict.keys(), key=int):
            timing = time_dict[key]
            audio_file = audio_path / f"snippet_{key}.mp3"

            if not audio_file.exists():
                _console.log(
                    f"[yellow]Warning: Missing narration file {audio_file}[/yellow]"
                )
                continue

            # Calculate relative timestamps
            start_time = timing["Start"] - time_dict["0"]["Start"]
            end_time = min(timing["End"] - time_dict["0"]["Start"], video.duration)

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
