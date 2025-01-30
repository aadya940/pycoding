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
        {', '.join([f'Path: {path}, Purpose: {purpose}' for path, purpose in self.path_info])}"""

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
