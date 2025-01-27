"""Class to create content using different vendors (Eg: Google)"""

from ._base import BaseAI
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
