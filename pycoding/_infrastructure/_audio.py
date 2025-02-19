from pathlib import Path
import time
from elevenlabs import VoiceSettings
from rich.console import Console

_console = Console()


class AudioManager:
    """Manage functions to generate elevenlabs audio."""

    def __init__(
        self, client, prompt_manager, model_object, voice_object, force_approve=False
    ):
        self.client = client
        self.prompt_manager = prompt_manager
        self.model_object = model_object
        self.voice_object = voice_object
        self.force_approve = force_approve

    def _generate_single_audio(self, code_snippet: str, path: str):
        """Generate audio for one snippet and save it."""
        _prompt = self.prompt_manager.get_audio_prompt(code_snippet)

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
        response = self.client.text_to_speech.convert(
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
