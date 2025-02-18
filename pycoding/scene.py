from pynput.keyboard import Controller
import pyautogui
import time


class CodingScene:
    def __init__(self, code_snippet, language, delay):
        self.code_snippet = code_snippet
        self.language = language
        self.delay = delay

    def type_code(self):
        keyboard = Controller()

        for idx in range(len(self.code_snippet)):
            indent_gap = None
            line = self.code_snippet[idx]

            if "python" in self.language:
                stripped_line = line.lstrip()
                next_line = (
                    self.code_snippet[idx + 1]
                    if (idx + 1) < len(self.code_snippet)
                    else None
                )
                curr_indent = len(line) - len(stripped_line)
                if next_line is not None:
                    next_indent = len(next_line) - len(next_line.lstrip())
                    indent_gap = next_indent - curr_indent
            else:
                stripped_line = line

            # Type each character with consistent timing
            for char in stripped_line:
                keyboard.press(char)
                time.sleep(self.delay)
                keyboard.release(char)
            pyautogui.press("enter")

            if indent_gap is not None:
                if indent_gap < 0:
                    for _ in range(-1 * indent_gap):
                        pyautogui.press("backspace")
