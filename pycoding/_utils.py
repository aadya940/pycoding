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
    max_width_ratio: float = 0.9,
    max_lines: int = 3,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    initial_font_scale: float = 6,
    thickness: int = 12,
    line_spacing: float = 1.2,
):
    """
    Generates a Vsauce-style text image with white text on a black background.

    Parameters:
    - text (str): The text to display.
    - output_file (str): The filename for the saved image.
    - image_size (tuple): Image dimensions (width, height) in pixels. Default is (1080, 1920) for 9:16 aspect ratio.
    - max_width_ratio (float): Maximum width ratio the text should occupy. Default is 0.9.
    - max_lines (int): Maximum number of lines before reducing font size. Default is 3.
    - font: OpenCV font type. Default is cv2.FONT_HERSHEY_SIMPLEX.
    - initial_font_scale (float): Starting font scale size. Default is 6.
    - thickness (int): Thickness of the text. Default is 12.
    - line_spacing (float): Spacing between lines. Default is 1.2x the text height.

    Returns:
    - Saves an image with the given text.
    """

    # Create a black image (9:16 aspect ratio)
    img = np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8)

    # Get approximate text size
    def get_text_size(txt, scale):
        return cv2.getTextSize(txt, font, scale, thickness)[0]

    # Auto-wrap text to fit within the image width
    wrapped_text = text
    font_scale = initial_font_scale
    while True:
        # Estimate text width
        lines = textwrap.wrap(text, width=30)  # Start with a reasonable guess
        text_sizes = [get_text_size(line, font_scale) for line in lines]

        # Check if the widest line fits within the max width
        max_text_width = max(size[0] for size in text_sizes)
        if (
            max_text_width <= image_size[0] * max_width_ratio
            and len(lines) <= max_lines
        ):
            wrapped_text = lines
            break

        # Reduce font size and try again
        font_scale -= 0.2
        if font_scale < 0.5:  # Prevent infinite loop
            break

    # Calculate total height of text block
    total_text_height = sum(size[1] for size in text_sizes) + (
        len(text_sizes) - 1
    ) * int(text_sizes[0][1] * line_spacing)

    # Calculate the starting Y position to center text
    y_offset = (image_size[1] - total_text_height) // 2

    # Draw each line on the image
    for line in wrapped_text:
        text_size = get_text_size(line, font_scale)
        text_x = (image_size[0] - text_size[0]) // 2  # Center horizontally
        text_y = y_offset + text_size[1]  # Move down per line
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
        y_offset += int(text_size[1] * line_spacing)  # Move down for the next line

    # Save the image instead of displaying it
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
