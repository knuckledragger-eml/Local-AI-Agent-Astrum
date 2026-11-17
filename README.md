# Astrum

A local AI agent that runs on your own hardware using Ollama. It can chat in the terminal, on Telegram, and via voice.

## Features
- Terminal chat with tool calling (web search, file listing)
- Telegram bot (so you can message it from your phone)
- Voice input (Whisper) + robotic text-to-speech (espeak)

## Requirements
- Ubuntu (tested on a Dell OptiPlex 7070)
- Python 3.11+
- Ollama with a model pulled (e.g. llama3.2:3b)
- System packages: sudo apt install espeak portaudio19-dev alsa-utils

## Setup
1. Clone the repo and enter the folder.
2. Create and activate a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
3. Install Python packages:
   pip install -r requirements.txt
   pip install "av<19"
4. Make sure Ollama is running and the model is available:
   ollama list

## Usage

### Terminal
python agent.py

### Telegram
1. Create a bot with @BotFather and get a token.
2. Edit telegram_bot.py and set TOKEN and ALLOWED_USER_ID.
3. Run: python telegram_bot.py

### Voice
1. Plug in a USB headset.
2. Check the device number:
   python -c "import sounddevice as sd; print(sd.query_devices())"
3. Set DEVICE = in voice_test.py to the correct number.
4. Run: python voice_test.py

## Troubleshooting
- PortAudio library not found: sudo apt install portaudio19-dev
- faster-whisper / av error: pip install "av<19"
- No sound / wrong device: Use arecord -l and python -c "import sounddevice as sd; print(sd.query_devices())"
- Telegram invalid token: Make sure you copied the full token from BotFather.
- Model not found: Run ollama list and use the exact name.

## Notes
This is a work-in-progress personal project for learning how local agents work.
