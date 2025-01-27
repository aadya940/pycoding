### Pycoding

An Agentic Python Library to create fully automated natural looking
python coding tutorial generation with audio narration. 

### Example

```bash
python3 -m pycoding --topic "Neural Network using Tensorflow" --io-path X.csv --io-path y.csv --google-api-key YOUR_GOOGLE_API_KEY --eleven-labs-api-key YOUR_ELEVEN_LABS_API_KEY --eleven-labs-voice-id YOUR_ELEVEN_LABS_VOIC_ID
```

This will generate a fully automated programming tutorial with narration based on user feedback 
teaching Neural Networks using Tensorflow.

### Supported Flags

```
--topic : Topic to make coding videos on.
--google-api-key : Google LLM API Key.
--elevenlabs-api-key : Eleven Labs Text to Speech API Key.
--elevenlabs-voice-id : Eleven Labs Voice ID for Text to Speech.
--io-path : Paths to directories you want to consider for code generation.
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
