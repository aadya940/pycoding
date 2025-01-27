from ._typing_scene import CodingTutorial
import argparse
from pathlib import Path
from rich import Console

# Initialize console for rich logging
_console = Console()

# Argument parser setup
parser = argparse.ArgumentParser(description="Paths for Coding Tutorial.")

parser.add_argument("--topic", type=str, required=True, help="Topic to make coding videos on.")
parser.add_argument(
    "--google-api-key", type=str, required=True, help="Google LLM API Key."
)
parser.add_argument(
    "--elevenlabs-api-key",
    type=str,
    required=True,
    help="Eleven Labs Text to Speech API Key.",
)
parser.add_argument(
    "--elevenlabs-voice-id",
    type=str,
    required=True,
    help="Eleven Labs Voice ID for Text to Speech.",
)
parser.add_argument(
    "--io-path",
    nargs="+",  # Fixed syntax error
    type=str,
    required=False,
    help="Paths to directories you want to consider for code generation.",
)

# Parse arguments
_args = parser.parse_args()

# Resolve and validate paths
if _args.io_path:
    resolved_paths = [Path(path).resolve() for path in _args.io_path]

    # Collect purposes for each path
    _purpose = []
    for _path in resolved_paths:
        if not _path.exists():
            raise ValueError(f"Incorrect Path: {_path}")

        _console.log(f"What is the purpose of the path {_path}?")
        _p = input("Enter purpose: ")
        _purpose.append(_p)

    # Combine paths and purposes
    path_info = [(_dir_path, _p) for _dir_path, _p in zip(resolved_paths, _purpose)]

    # Log collected path information
    _console.log("[green]Collected Path Information:[/green]")
    for path, purpose in path_info:
        _console.log(f"  Path: {path} -> Purpose: {purpose}")
else:
    path_info = []
    _console.log("[yellow]No paths provided. Skipping path setup.[/yellow]")

_tutorial = CodingTutorial(
    eleven_labs_api_key=_args.elevenlabs_api_key,
    eleven_labs_voice_id = _args.elevenlabs_voice_id,
    google_api_key=_args.google_api_key,
    path_info=path_info,
)
_tutorial.make_tutorial()
