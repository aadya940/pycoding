# **Pycoding**

[Example Tutorial](https://github.com/user-attachments/assets/2f059979-9a68-4dc3-8942-b0a3ff3f1b8d)



## **Automated Coding Tutorial Generation with Audio Narration**

**Pycoding** is an agentic Python library designed to generate fully automated, natural-looking coding tutorials with real-time or post-processed audio narration. It combines AI-powered code generation, screen recording, and voice synthesis to create engaging programming tutorials.

---

## **Key Features**

- **AI-Powered Code Generation**: Uses Google's Generative AI to create relevant code examples
- **Natural Voice Narration**: Integrates with ElevenLabs for high-quality voice synthesis
- **Real-Time Screen Recording**: Captures live coding demonstrations
- **Multi-Language Support**: Works with multiple programming languages
- **Flexible Narration Modes**: Supports both real-time and post-processed narration
- **Title Slide Generation**: Optional title slides for each code segment
- **Automated Window Management**: Handles Jupyter console and matplotlib windows automatically

## **Supported Languages**

Pycoding supports generating tutorials in the following programming languages:

- **Python** (`python3`)
- **C/C++** (`xcpp17`)
- **Julia** (`julia`)
- **Rust** (`rust`)
- **Bash** (`bash`)
- **R** (`r`)

---

## **Prerequisites**

Before installing Pycoding, ensure you have the following:

### **System Requirements**
- Linux operating system (currently Linux-only)
- `ffmpeg` for audio/video processing
- `wmctrl` and `xwininfo` for window management
- `gnome-terminal` for terminal emulation
- Jupyter installation with required language kernels

### **API Requirements**
- Google Generative AI API key
- ElevenLabs API key and voice ID

### **Python Dependencies**
Core dependencies include:
```
ffmpeg-python
google-generativeai
pydub
simpleaudio
pyautogui
pynput
rich 
elevenlabs
jupyter
ipython
pycaw
comtypes
pygetwindow
moviepy
opencv-python
```

---

## **Installation**

1. **Clone the Repository**
```bash
git clone https://github.com/your-repo/pycoding.git
cd pycoding
```

2. **Install Dependencies**
```bash
python3 -m pip install -r requirements.txt
```

3. **Install the Library**
```bash
python3 -m pip install .
```

4. **Configure Jupyter Kernels**
See [README_kernels.md](README_kernels.md) for detailed instructions on setting up language kernels.

---

## **Usage**

### **Command Line Interface**

Generate a coding tutorial using the command line:

```bash
python3 -m pycoding \
    --topic "Your Tutorial Topic" \
    --google-api-key YOUR_GOOGLE_API_KEY \
    --elevenlabs-api-key YOUR_ELEVENLABS_API_KEY \
    --elevenlabs-voice-id YOUR_ELEVENLABS_VOICE_ID \
    --narration-type parallel \
    --language python3
    --force-approve
    --add-titles
```

### **Python API**

```python
from pycoding import CodingTutorial, GoogleGenAI

# Initialize AI model
model = GoogleGenAI(google_api_key)

# Create tutorial
tutorial = CodingTutorial(
    topic="Your Tutorial Topic",
    eleven_labs_api_key="YOUR_ELEVENLABS_API_KEY",
    eleven_labs_voice_id="YOUR_ELEVENLABS_VOICE_ID",
    model_object=model,
    path_info=[],  # Optional paths for code context
    narration_type="parallel",  # or "after"
    language="python3",
    force_approve=False,  # Set to True to skip manual approvals
    add_titles=True  # Add title slides
)

# Generate the tutorial
tutorial.make_tutorial()
```

### **Command Line Options**

| **Flag**                   | **Description** |
|----------------------------|----------------|
| `--topic`                  | Tutorial topic |
| `--google-api-key`         | Google Generative AI API key |
| `--elevenlabs-api-key`     | ElevenLabs API key |
| `--elevenlabs-voice-id`    | ElevenLabs voice ID |
| `--io-path`                | Paths for code context (optional) |
| `--narration-type`         | Narration mode: `parallel` or `after` |
| `--language`               | Programming language |
| `--force-approve`          | Skip manual approvals |
| `--add-titles`             | Add title slides |

---

## **Output**

The generated tutorial includes:
- Screen recording of code typing and execution
- AI-generated voice narration
- Optional title slides
- Synchronized audio and video
- Output files in `pycoding_data/` directory

---

## **Examples**

### **Basic Python Tutorial**
```bash
python3 -m pycoding \
    --topic "Python List Comprehensions in 3 Examples" \
    --google-api-key YOUR_KEY \
    --elevenlabs-api-key YOUR_KEY \
    --elevenlabs-voice-id YOUR_ID \
    --language python3
```

### **C++ Tutorial with Titles**
```bash
python3 -m pycoding \
    --topic "Understanding C++ Templates" \
    --google-api-key YOUR_KEY \
    --elevenlabs-api-key YOUR_KEY \
    --elevenlabs-voice-id YOUR_ID \
    --language xcpp17 \
    --add-titles
```

---

## **Limitations**

- Currently supports Linux environments only
- Requires specific window management utilities
- API keys needed for AI services
- Language kernels must be properly configured

---

## **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

---

## **Author**

Aadya Chinubhai
