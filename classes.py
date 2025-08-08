import pyaudio
import pvporcupine
import struct
import wave
import os
import random
from piper import PiperVoice
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv
import speech_recognition as sr
import numpy as np
import yt_dlp
import tempfile
import fastapi


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
pcup_access = os.getenv("pcup_access")
path_to_wake = os.getenv("path_to_wake")
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
scope = "user-modify-playback-state user-read-playback-state"

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

        self.responding = False

        self.context = []

        self.reactions = ("/home/freddy-berg/CARL/reactions/yes.wav","/home/freddy-berg/CARL/reactions/huh.wav","/home/freddy-berg/CARL/reactions/whats_up.wav" )

        self.pauses = ("/home/freddy-berg/CARL/pauses/erm.wav", "/home/freddy-berg/CARL/pauses/uhh.wav", "/home/freddy-berg/CARL/pauses/umm.wav")

        self.music_remarks = [
            "What a good tune. Is there anything else you'd like me to play?",
            "Another song, perhaps?",
            "Which one would you like me to play now?",
            "Which song now?"
        ]

    def detect_word(self):
        print("listening for 'hey carl'")
        with self.audio.input_stream(
            rate=self.porcupine.sample_rate,
            frames_per_buffer=self.porcupine.frame_length
        ) as stream:
            
            i = 0
            while True:

                pcm = stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                keyword_detection = self.porcupine.process(pcm)

                if keyword_detection >= 0:
                    self.responding = True
                    return
                else:
                    pass

    def play_wav_file(self, file_path):

        if os.path.exists(file_path):
            with wave.open(file_path, 'rb') as wf:
                params = wf.getparams()
            
                rate=params.framerate
                channels=params.nchannels
                sample_width = params.sampwidth

                with self.audio.output_stream(
                    rate=rate,
                    channels=channels,
                    format=self.audio.pa.get_format_from_width(sample_width)
                ) as stream:
                                
                    # Read and play audio in chunks
                    chunk_size = 1024
                    data = wf.readframes(chunk_size)

                    while data:
                        stream.write(data)
                        data = wf.readframes(chunk_size)
            return
        
        else: 
            print("WAV file not found")
            return(1)
    
    def speak(self, statement):

        try:
            voice = PiperVoice.load("/home/freddy-berg/CARL/voice_files/en_GB-alan-medium.onnx")
            with wave.open("output.wav", "wb") as f:
                voice.synthesize_wav(statement, f)

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
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 1.1
            r.non_speaking_duration = .08
            print("Speak")
            audio = r.listen(source, timeout=1.2, phrase_time_limit=20)
        try:
            text = r.recognize_openai(audio)
        except sr.RequestError as e:
            print(e)

        return text

    def load_context(self, text, role):
        self.context.append({
            "role": role,
            "content": text
        })
        return
        
    def generate_response(self, result_dict, id):
        response  = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=self.context
        )
        
        finish_reason = response.choices[0].finish_reason
        if finish_reason != "stop":
            self.speak("I'm sorry, my mind is gone because it's not connected to Sam Altman's basilisk god. Fix me plaese.")
            return

        result_dict[id] = response.choices[0].message.content

        return
        
    def parse_response(self, response):
        
        self.load_context(response, "assistant")
        
        text = ''
        function = '' 
        args = ['']
        i = 0
        twoargs = False
        while response[i] != '#':
            text += response[i]
            i += 1
        i += 1
        self.speak(text)
        while response[i] != '(':
            function += response[i]
            i += 1
        i += 1
        while response [i] != ")":
            if twoargs == True:
                args[1] += response[i]
                i += 1
            else:
                if response[i] == ",":
                    twoargs = True
                    args.append("")
                    i += 1
                else:
                    args[0] += response[i]
                    i += 1
        

        if function == "none":
            return()
        elif function == "play_music":
            return(self.play_music(args[0], args[1]))
        elif function == "lookup":
            return(self.lookup(args[0]))
        elif function == "deactivate":
            self.responding = False
            return()
        else: 
            return()

    def play_music(self, song, artist):
        
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  
            }],
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{artist} {song}"
            info = ydl.extract_info(search_query, download=True)
            if info['entries']:
                entry = info['entries'][0]
                filename = ydl.prepare_filename(entry)
                wav_filename = os.path.splitext(filename)[0] + '.wav'

                self.play_wav_file(wav_filename)
                
                remark = random.choice(self.music_remarks)
                self.speak(remark)
                self.load_context(remark, "assistant")
                return
            
            else:
                print("song not found")
                return(1)

    def pause(self):
        pause = random.choice(self.pauses)
        self.play_wav_file(pause)
        return

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
        self.speak(summarized.output_text)
        return summarized.output_text
        
    def make_soundfile(self, text, filename):
        try:
            voice = PiperVoice.load("/home/freddy-berg/CARL/voice_files/en_GB-alan-medium.onnx")
            with wave.open(filename, "wb") as f:
                voice.synthesize_wav(text, f)

        except Exception as e:
            print(f"error: {e}")

        # Play file over speaker
        self.play_wav_file(filename)

