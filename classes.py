import pyaudio
import pvporcupine
import struct
import wave
import os
import subprocess
import random
import piper
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
gpt_api = os.getenv("gpt_api")
pcup_access = os.getenv("pcup_access")
path_to_wake = os.getenv("path_to_wake")

class AudioHandler:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
    
    def input_stream(self, rate=44100, channels=1, frames_per_buffer=1024):
        class InputStreamContext:
            def __init__(self, pa, rate, channels, frames_per_buffer):
                self.pa = pa
                self.rate = rate
                self.channels = channels
                self.frames_per_buffer = frames_per_buffer
                self.stream = None
            
            def __enter__(self):
                self.stream = self.pa.open(
                    rate=self.rate,
                    channels=self.channels,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.frames_per_buffer,
                    input_device_index=None
                )
                return self.stream
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()

        return InputStreamContext(self.pa, rate, channels, frames_per_buffer)      


    def output_stream(self, rate=44100, channels=1, format = pyaudio.paInt16):
        class OutputStreamContext:
            def __init__(self, pa, rate, channels, format):
                self.pa = pa
                self.rate = rate
                self.channels = channels
                self.format = format
                self.stream = None
            
            def __enter__(self):
                self.stream = self.pa.open(
                    rate=self.rate,
                    channels=self.channels,
                    format=self.format,
                    output=True
                )
                return self.stream
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
        
        return OutputStreamContext(self.pa, rate, channels, format)


class Assistant:
    
    def __init__(self):

        self.porcupine = pvporcupine.create(
           access_key=pcup_access,
           keyword_paths=[path_to_wake]
        )

        self.audio = AudioHandler()

        self.client = OpenAI()

        prompt = ''
        with open("/home/freddy-berg/CARL/sys_prompt.txt", "r") as file:
            prompt = file.read()
        
        self.default_context = [
            {
                "role":"developer",
                "content": prompt
            }
        ]

        self.context = []

        self.reactions = ("/home/freddy-berg/CARL/reactions/yes.wav","/home/freddy-berg/CARL/reactions/huh.wav","/home/freddy-berg/CARL/reactions/whats_up.wav" )

    def detect_word(self):

        with self.audio.input_stream(
            rate=self.porcupine.sample_rate,
            frames_per_buffer=self.porcupine.frame_length
        ) as stream:

            pcm = stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_detection = self.porcupine.process(pcm)
      
            if keyword_detection >= 0:
                return(True)
            else:
                return(False)
        
    def shutdown(self):
        pass

    def play_wav_file(self, file_path):

        if os.path.exists(file_path):
            wf = wave.open(file_path, 'rb')

            with self.audio.output_stream(
                rate=wf.getframerate(),
                channels=wf.getnchannels(),
                format=self.audio.pa.get_format_from_width(wf.getsampwidth())
            ) as stream:
    
                # Read and play audio in chunks
                chunk_size = 1024
                data = wf.readframes(chunk_size)

                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)

            wf.close()

        else:
            print("WAV file not found")
            return 1


    def speak(self, statement):

        try:
            subprocess.run([
                "piper", 
                "--model", "en_GB-alan-medium",
                "--output_file", "output.wav"
            ], input=statement, text=True)
        except Exception as e:
            print(f"error: {e}")

        # Play file over speaker
        self.play_wav_file("output.wav")
        
        # Delete file
        os.remove("output.wav")

    def react(self):
        reaction = random.choice(self.reactions)
        self.play_wav_file(reaction)
        return

    def listen(self):

        pass

    def load_context(self, text, role):
        self.context.append({
            "role": role,
            "content": text
        })
        return
        

    def generate_response(self, context):
        response  = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=context
        )
        
        finish_reason = response.choices[0].finish_reason
        if finish_reason != "stop":
            self.speak("I'm sorry, my mind is gone because it's not connected to Sam Altman's basilisk god. Fix me plaese.")
            return

        text = response.choices[0].message.content
        self.load_context(text, "assistant")

        return text
        
        

    def analyze_response(self, response):
        
        pass

    def play_music(self, song, artist):
        #uses spotify API to play music
        pass

    def lookup(self, phrase):
        response = self.client.responses.create(
            model="gpt-4.1",
            tools=[{ "type": "web_search_preview" }],
            input=phrase
        )
        summarized = self.client.responses.create(
            model="gpt-4.1",
            instructions="summarize this text in a few English scentances. No need to cite sources.",
            input = response.output_text
        )
        self.load_context(summarized.output_text, "assistant")
        return summarized.output_text

        
        

