import speech_recognition as sr
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# obtain audio from the microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source)

try:
    print(f"OpenAI Whisper API thinks you said {r.recognize_openai(audio)}")
except sr.RequestError as e:
    print(f"Could not request results from OpenAI Whisper API; {e}")




