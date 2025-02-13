# **Pycoding**

## **Automated Coding Tutorial Generation with Audio Narration**

**Pycoding** is an agentic Python library designed to generate fully automated, natural-looking coding tutorials with real-time or post-processed audio narration.

---

## **Supported Languages**

Pycoding supports generating tutorials in the following programming languages:

- **Python**  
- **C/C++**  
- **Julia**  
- **Rust**  
- **Bash**  
- **R**  

---

## **Usage Example**

To generate a coding tutorial on "Classes in Python in 3 lines" with narration, run the following command:

```bash
python3 -m pycoding --topic \  
"Classes in Python in 3 lines." \  
--google-api-key YOUR_GOOGLE_API_KEY \  
--elevenlabs-api-key YOUR_ELEVENLABS_API_KEY \  
--elevenlabs-voice-id YOUR_ELEVENLABS_VOICE_ID \  
--narration-type parallel \  
--language python3
```

This command will produce a fully automated programming tutorial, including both code and narration.

---

## **Examples**

### **NDArray Operations in NumPy**  
🔗 [Example Tutorial](https://github.com/user-attachments/assets/39f2cc45-4c08-46dd-bbe6-6519c0331f2c)  

---

## **Command-Line Flags**

| **Flag**                   | **Description** |
|----------------------------|----------------|
| `--topic`                  | Topic for the coding tutorial. |
| `--google-api-key`         | API key for Google LLM. |
| `--elevenlabs-api-key`     | API key for Eleven Labs Text-to-Speech. |
| `--elevenlabs-voice-id`    | Voice ID for Eleven Labs narration. |
| `--io-path`                | Directory paths to consider for code generation. |
| `--narration-type`         | Narration mode: `parallel` (during typing) or `after` (post-processing). |
| `--force-approve`          | Automatically approve all AI-generated responses. |
| `--language`               | Programming language for the tutorial (use `jupyter kernelspec list` for available options). |

---

## **Installation & Setup**

### **Requirements**  
Ensure you have the following installed before using Pycoding:

- `ffmpeg`  
- A **Google Generative AI** account  
- An **Eleven Labs** account  
- `Jupyter`, `Required Language Jupyter Kernel (Look at README_kernels.md)`.   
- Linux utilities: `wmctrl`, `xwininfo`, `gnome-terminal`, `jupyter`  

### **Installation**

```bash
# Clone the repository
git clone https://github.com/your-repo/pycoding.git
cd pycoding

# Install dependencies
python3 -m pip install -r requirements.txt

# Install Library
python3 -m pip install .
```

---

## **Limitations**

- **Linux Only**: Currently, Pycoding only supports Linux-based environments.

