import re
from pydub import AudioSegment
from pydub.playback import play


def parse_code(text):
    """Parse the first code snippet containing triple backticks."""
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", text, re.DOTALL)
    _list = [{"language": lang, "code": code.strip()} for lang, code in code_blocks]
    _snippets = [iter_["code"] for iter_ in _list]
    return _snippets


def _play_audio_on_cell_execution(audio_file):
    """Play an audio file after a code cell is executed using pydub."""
    audio = AudioSegment.from_file(audio_file)
    play(audio)  # Play the audio file.
