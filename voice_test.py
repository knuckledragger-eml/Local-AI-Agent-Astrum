import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import requests
import json
import subprocess


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"
SAMPLE_RATE = 48000
RECORD_SECONDS = 5
DEVICE = 5  # your audio device

print("Loading Whisper model...")
whisper = WhisperModel("tiny.en", device="cpu", compute_type="int8")

def record_audio(seconds=RECORD_SECONDS):
    print(f"Recording for {seconds} seconds... speak now")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16", device=DEVICE)
    sd.wait()
    from scipy.io.wavfile import write
    write("temp_voice.wav", SAMPLE_RATE, audio)
    return "temp_voice.wav"

def transcribe(audio_file):
    segments, _ = whisper.transcribe(audio_file, language="en")
    text = " ".join([seg.text for seg in segments]).strip()
    return text

def speak(text):
    subprocess.run(["espeak", "-s", "130", "-v", "en", text])

def ask_astrum(user_message: str) -> str:
    messages = [{
        "role": "system",
        "content": """You are Astrum, a helpful local agent.
You have tools, but only use them when you need external or real-time information you don't already know.
For questions about yourself, your name, or general knowledge, just answer directly.
When you do need a tool, reply with ONLY JSON like:
{"tool": "web_search", "args": {"query": "your search"}}
or
{"tool": "list_files", "args": {"path": "."}}
After getting a tool result, give a normal final answer. Do not call the tool again."""
    }, {"role": "user", "content": user_message}]

    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages, "stream": False})
    reply = resp.json()["message"]["content"]
    return reply

def main():
    print("Astrum voice test ready.")
    print("Press Enter to record, or type 'quit' to exit.")
    while True:
        cmd = input("\nPress Enter to speak (or 'quit'): ").strip()
        if cmd.lower() in ("quit", "exit"):
            break
        audio = record_audio()
        text = transcribe(audio)
        print(f"You said: {text}")
        if text:
            answer = ask_astrum(text)
            print(f"Astrum: {answer}")
            speak(answer)
        else:
            print("No speech detected.")

if __name__ == "__main__":
    main()

