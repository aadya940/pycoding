### Pycoding

An Agentic Python Library to create fully automated natural looking coding tutorial generation with audio narration. 

Supported languages:

```
Python
C/C++
Julia
Rust
Bash
R
```

### Code Example

```bash
python3 -m pycoding --topic "Neural Network using Tensorflow" --io-path X.csv y.csv --google-api-key YOUR_GOOGLE_API_KEY --elevenlabs-api-key YOUR_ELEVENLABS_API_KEY --elevenlabs-voice-id YOUR_ELEVENLABS_VOICE_ID
```

This will generate a fully automated programming tutorial with narration based on user feedback teaching Neural Networks using Tensorflow.

### Examples

NDArrays in Numpy:

https://github.com/user-attachments/assets/09a1bf87-8553-4999-ad4f-bd889896fbb9


### Supported Flags

```
--topic : Topic to make coding videos on.
--google-api-key : Google LLM API Key.
--elevenlabs-api-key : Eleven Labs Text to Speech API Key.
--elevenlabs-voice-id : Eleven Labs Voice ID for Text to Speech.
--io-path : Paths to directories you want to consider for code generation.
--narration-type : either `after` or `parallel`. Specifies if  Narration 
has to happen during or after code typewriting.
--force-approve : Approve all AI responses to `yes` by default.
```

### Set Up

```
Requires:
- ffmpeg.
- A eleven labs and Google Generative AI Account.
- Requires IPython.
- Requires wmctrl, xwininfo, gnome-terminal, ipython, pactl shell commands.
```
```
- Clone.
- `python3 -m pip install -r requirements.txt`
- Use :)
```
```
Limitations:
- Completely Linux Based.
```
