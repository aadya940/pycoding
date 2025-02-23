import re
from pydub import AudioSegment
import psutil
import cv2
import numpy as np
import textwrap
import os


def create_title(
    text: str,
    output_file: str,
    image_size: tuple = (1080, 1920),
    max_width_ratio: float = 0.8,  # Slightly reduced to prevent text getting too close to edges
    max_lines: int = 3,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    initial_font_scale: float = None,  # Will be calculated based on image height
    thickness: int = None,  # Will be calculated based on image height
    line_spacing: float = 1.2,
):
    """
    Generates a Vsauce-style text image with white text on a black background.
    The text size and thickness are automatically scaled based on the image dimensions.

    Parameters:
    - text (str): The text to display.
    - output_file (str): The filename for the saved image.
    - image_size (tuple): Image dimensions (width, height) in pixels.
    - max_width_ratio (float): Maximum width ratio the text should occupy. Default is 0.8.
    - max_lines (int): Maximum number of lines before reducing font size. Default is 3.
    - font: OpenCV font type. Default is cv2.FONT_HERSHEY_SIMPLEX.
    - initial_font_scale (float): Starting font scale size. If None, calculated from image height.
    - thickness (int): Thickness of the text. If None, calculated from image height.
    - line_spacing (float): Spacing between lines. Default is 1.2x the text height.

    Returns:
    - str: Absolute path to the created image file.
    """
    # Create a black image
    img = np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8)

    # Calculate initial font scale and thickness based on image height if not provided
    if initial_font_scale is None:
        initial_font_scale = image_size[1] * 0.003  # 0.3% of image height
    if thickness is None:
        thickness = max(1, int(image_size[1] * 0.006))  # 0.6% of image height

    # Get approximate text size
    def get_text_size(txt, scale):
        return cv2.getTextSize(txt, font, scale, thickness)[0]

    # Auto-wrap text to fit within the image width
    font_scale = initial_font_scale
    while True:
        # Calculate maximum characters per line based on current font scale
        test_width = get_text_size("W" * 50, font_scale)[
            0
        ]  # Use 'W' as it's typically the widest character
        chars_per_line = int(50 * (image_size[0] * max_width_ratio) / test_width)

        # Wrap text
        lines = textwrap.wrap(text, width=chars_per_line)
        text_sizes = [get_text_size(line, font_scale) for line in lines]

        # Check if text fits
        max_text_width = max(size[0] for size in text_sizes)
        if (
            max_text_width <= image_size[0] * max_width_ratio
            and len(lines) <= max_lines
        ):
            break

        # Reduce font size and try again
        font_scale *= 0.9
        if font_scale < 0.1:  # Prevent infinite loop
            font_scale = 0.1
            break

    # Calculate total height of text block
    line_height = max(size[1] for size in text_sizes)
    total_text_height = line_height * len(lines) + (len(lines) - 1) * int(
        line_height * (line_spacing - 1)
    )

    # Calculate starting Y position to center text block
    y_offset = (image_size[1] - total_text_height) // 2

    # Draw each line
    for line in lines:
        text_size = get_text_size(line, font_scale)
        text_x = (image_size[0] - text_size[0]) // 2  # Center horizontally
        text_y = y_offset + text_size[1]  # Position vertically

        cv2.putText(
            img,
            line,
            (text_x, text_y),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            lineType=cv2.LINE_AA,
        )
        y_offset += int(line_height * line_spacing)

    # Save the image
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    cv2.imwrite(output_file, img)
    return os.path.abspath(output_file)


def _get_audio_length(audio_file):
    """Returns length of the audio in seconds."""
    audio = AudioSegment.from_file(audio_file)
    return len(audio) / 1000


def _is_jupyter_idle(proc):
    """Check if the IPython process is idle by monitoring its CPU usage."""
    try:
        p = psutil.Process(proc.pid)
        # Get all child processes
        children = p.children(recursive=True)

        # Check CPU usage of main process and all children
        total_cpu = p.cpu_percent(interval=0.1)
        for child in children:
            try:
                total_cpu += child.cpu_percent(interval=0.1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return total_cpu < 5.0  # Higher threshold for combined CPU usage

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True  # If process is gone or inaccessible, consider it done


def parse_code(text):
    """Parse the first code snippet containing triple backticks."""
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", text, re.DOTALL)
    _list = [{"language": lang, "code": code.strip()} for lang, code in code_blocks]
    _snippets = [iter_["code"] for iter_ in _list]
    return _snippets


def needs_flowchart(code_snippet: str) -> bool:
    """
    Determines if a code snippet would benefit from a flowchart visualization.

    Returns True if the code contains:
    - Control flow statements (if/else, loops)
    - Function definitions with multiple paths
    - Complex algorithms or data transformations
    """
    # Keywords that suggest control flow or complex logic
    flow_indicators = {
        "if",
        "else",
        "elif",
        "for",
        "while",
        "try",
        "except",
        "match",
        "case",
        "def",
        "class",
        "return",
        "yield",
        "break",
        "continue",
    }

    # Check for presence of flow control keywords, excluding commented lines
    has_flow_control = False
    for line in code_snippet.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            # Check if any flow indicator is present in this non-commented line
            if any(
                f" {keyword} " in f" {line.lower()} " for keyword in flow_indicators
            ):
                has_flow_control = True
                break

    # Return True if there's control flow or the code is complex enough
    return has_flow_control
