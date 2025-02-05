import re
from pydub import AudioSegment
import psutil


def _get_audio_length(audio_file):
    """Returns length of the audio in seconds."""
    audio = AudioSegment.from_file(audio_file)
    return len(audio) / 1000


def _is_jupyter_idle(proc):
    """Check if the IPython process is idle by monitoring its CPU usage."""
    try:
        p = psutil.Process(proc.pid)
        cpu_usage = p.cpu_percent(interval=0.1)  # Get CPU usage
        return cpu_usage < 1  # If CPU usage is very low, assume idle
    except psutil.NoSuchProcess:
        return True  # If the process is gone, it's done


def parse_code(text):
    """Parse the first code snippet containing triple backticks."""
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", text, re.DOTALL)
    _list = [{"language": lang, "code": code.strip()} for lang, code in code_blocks]
    _snippets = [iter_["code"] for iter_ in _list]
    return _snippets
