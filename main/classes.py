import pyaudio
import pvporcupine
import keys
import struct
import wave
import os
import subprocess


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
           access_key=keys.pcup_access,
           keyword_paths=[keys.path_to_wake]
        )

        self.audio = AudioHandler()

        self.default_context = {
            
        }

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

    def play_wav_file(self, filename):
        # Open the WAV file
        wf = wave.open(filename, 'rb')

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


    def speak(self, statement):

        subprocess.run([
            "piper", 
            "--model", "en_US-danny-low",
            "--output_file", "output.wav"
        ], input=statement, text=True)
        
        # Play file over speaker
        self.play_wav_file("output.wav")
        
        # Delete file
        os.remove("output.wav")


    def listen(self):
        pass
        

    def translate(self, audio_file):
        #takes in audio file of human speech and turns it into text
        pass

    def generate_response(self, text):
        #uses Chatgpt API to generate a response to given text.
        pass

    def analyze_response(self, response):
        
        pass

    def play_music(self, song, artist):
        #uses spotify API to play music
        pass

    def lookup(self, query):
        #uses google API to look up facts
        pass

carl = Assistant()

carl.speak("I am Carl, your personal AI assistant.")