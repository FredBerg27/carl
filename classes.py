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
import pygame
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

def generate_white_noise(duration,  sample_rate=44100):
    num_samples = int(duration * sample_rate)
    
    # Generate random noise between -1 and 1
    static = np.random.uniform(-1.0, 1.0, num_samples)

    static_int16 = (static * 32767).astype(np.int16)
    
    return static_int16

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
                if i % 5000 == 0 and i >= 5000:
                    print("maintaining bluetooth connection")
                    self.play_wav_file("/home/freddy-berg/CARL/static/quiet_static.wav")
                else:
                    pass

                if keyword_detection >= 0:
                    self.responding = True
                    return
                else:
                    i += 1
                    print(i)
                    pass

    def play_wav_unbuffered(self, file_path):

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
    
    def play_wav_file(self, file_path):

        if os.path.exists(file_path):
            with wave.open(file_path, 'rb') as wf:
                params = wf.getparams()
                n_frames = params.nframes
                frames = wf.readframes(n_frames)

            rate=params.framerate
            channels=params.nchannels
            sample_width = params.sampwidth

            if sample_width == 2:  # 16-bit
                audio_data = np.frombuffer(frames, dtype=np.int16)
            elif sample_width == 4:  # 32-bit
                audio_data = np.frombuffer(frames, dtype=np.int32)
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")

            static = generate_white_noise(.250, rate)

            max_amplitude = np.max(np.abs(audio_data))
            static = static * .001 * max_amplitude / np.max(np.abs(static))

            if channels == 2:
                # Reshape original audio for stereo
                audio_data = audio_data.reshape(-1, 2)
                # Create stereo static by duplicating mono static
                static_stereo = np.column_stack([static, static])
                # Concatenate audio and static
                combined_audio = np.vstack([audio_data, static_stereo])
                # Flatten back to 1D array
                combined_audio = combined_audio.flatten()
            else:
                # Mono: just concatenate
                combined_audio = np.concatenate([static, audio_data])

            if audio_data.dtype == np.int16:
                combined_audio = np.clip(combined_audio, -max_amplitude, max_amplitude)
                combined_audio = combined_audio.astype(np.int16)

            with wave.open("buffered.wav", "wb") as wf:
                wf.setparams(params)
                wf.writeframes(combined_audio.tobytes())
            
            with wave.open("buffered.wav", "rb") as wf:
                with self.audio.output_stream(
                    rate=rate,
                    channels=channels,
                    format=self.audio.pa.get_format_from_width(wf.getsampwidth())
                ) as stream:
                                
                    # Read and play audio in chunks
                    chunk_size = 1024
                    data = wf.readframes(chunk_size)

                    while data:
                        stream.write(data)
                        data = wf.readframes(chunk_size)
            
            os.remove("buffered.wav")

        else:
            print("WAV file not found")
            return 1

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
            audio = r.listen(source, timeout=1, phrase_time_limit=20)
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
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{artist} {song}"
            info = ydl.extract_info(search_query, download=False)
            if info['entries']:
                url = info['entries'][0]['url']
                pygame.mixer.init()
                pygame.mixer.music.load(url)
                pygame.mixer.music.play()
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

