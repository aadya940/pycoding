"""Class to create content using different vendors (Eg: Google)"""

from .._base import BaseAI
import google.generativeai as genai


class GoogleGenAI(BaseAI):
    def __init__(self, api_key, model="gemini-2.0-flash-exp"):
        """Initialization with default model and location."""
        self.api_key = api_key

        # Configure the API with key and location
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.chat = None  # Placeholder for the chat session

    def start_chat(self, history=None):
        """Start a chat session with Gemini."""
        if history is None:
            history = []  # Default to an empty chat history

        self.chat = self.model.start_chat(
            history=history,
        )

    def send_message(self, message):
        """Send a message in the chat session."""
        if self.chat is None:
            raise ValueError("Call `start_chat` before sending a message.")

        response = self.chat.send_message(message)
        return response.text  # Extract the response content

class PromptManager:
    def __init__(self, language, topic, path_info=None):
        self._language = language.lower()  # Fix incorrect `_language`
        self.topic = topic
        self.path_info = path_info or []

    def build_prompt(self):
        if "python" in self._language:
            return self._python_prompt()

        elif "cpp" in self._language:
            return self._cpp_prompt()

        elif ("r" in self._language) and (len(self._language) < 3):
            return self._r_prompt()

        elif "julia" in self._language:
            return self._julia_prompt()

        elif "rust" in self._language:
            return self._rust_prompt()

    def _python_prompt(self):
        return f"""Write Python code snippets to explain the following topic. 
        Write only well-commented code snippets, and ensure each snippet is under 30 seconds to read.

        **Topic:**  
        {self.topic}

        **Instructions:**  
        1. Split the code into multiple ```python your_code ``` blocks.  
        2. Each block should be well-commented, focusing on clarity and explanation.  
        3. Use or consider the following paths and their associated purposes in the code:  
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}
        4. Make sure the code doesn't take more than 5 minutes to run. For example, if you're
        teaching machine learning with tensorflow, run the model for only one epoch. Hope you
        get the point.
        """

    def _cpp_prompt(self):
        return f"""Write C++ code snippets to explain the following topic. 
        Write only well-commented code snippets, ensuring each snippet is under 30 seconds to read.

        **Topic:**  
        {self.topic}

        **Instructions:**  
        1. Split the code into multiple ```cpp your_code ``` blocks.  
        2. Each block should be well-commented, with clear explanations of key concepts.  
        3. Use or consider the following paths and their associated purposes in the code:  
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}
        4. Use Cling-specific pragmas when necessary, e.g.:
        #pragma cling add_include_path("your/path")
        #pragma cling load("your_library")
        5. Ensure compatibility with the Cling compiler.
        6. Use quotes instead of angle brackets while import any headers in the code.
        """

    def _r_prompt(self):
        return f"""Write R code snippets to explain the following topic. 
        Write only well-commented code snippets, ensuring each snippet is under 30 seconds to read.

        **Topic:**  
        {self.topic}

        **Instructions:**  
        1. Split the code into multiple ```r your_code ``` blocks.  
        2. Each block should be well-commented, focusing on clarity and explanation.  
        3. Use or consider the following paths and their associated purposes in the code:  
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}"""

    def _julia_prompt(self):
        return f"""Write Julia code snippets to explain the following topic. 
        Write only well-commented code snippets, ensuring each snippet is under 30 seconds to read.

        **Topic:**  
        {self.topic}

        **Instructions:**  
        1. Split the code into multiple ```julia your_code ``` blocks.  
        2. Each block should be well-commented, focusing on clarity and explanation.  
        3. Use or consider the following paths and their associated purposes in the code:  
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}"""

    def _rust_prompt(self):
        return f"""Write Rust code snippets to explain the following topic. 
        Write only well-commented code snippets, ensuring each snippet is under 30 seconds to read.

        **Topic:**  
        {self.topic}

        **Instructions:**  
        1. Split the code into multiple ```rust your_code ``` blocks.  
        2. Each block should be well-commented, focusing on clarity and explanation.  
        3. Use or consider the following paths and their associated purposes in the code:  
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}
        4. Ensure compatibility with `Evcxr` rust kernel.
        """

    def get_audio_prompt(self, code_snippet):
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
        return _prompt

