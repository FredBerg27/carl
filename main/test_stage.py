import pyaudio
import pvporcupine
import keys
import struct


class Ai:
    def __init__(self):

        self.porcupine = pvporcupine.create(
           access_key=keys.pcup_access,
           keyword_paths=[keys.path_to_wake])

        self.pa = pyaudio.PyAudio()
        
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
            input_device_index=None  # Use default input device
        )

    def detect_word(self):
        
        pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
        keyword_detection = self.porcupine.process(pcm)
      
      
        if keyword_detection >= 0:
            return(True)
        else:
            return(False)
        
    def shutdown(self):
     if self.audio_stream:
         self.audio_stream.stop_stream()
         self.audio_stream.close()
     if self.pa:
         self.pa.terminate()
     if self.porcupine:
         self.porcupine.delete()