
import pvporcupine
import pyaudio
import struct

access_key = "QDvMT9ImmgTsLR7E7793aAhHR6PVHQh4C8c/PBOlsewNqIJRuoUxcg=="

porcupine = None
pa = None
audio_stream = None

porcupine = pvporcupine.create(
   access_key=access_key,
   keyword_paths=['/home/freddy-berg/CARL/wake_files/hey-carl.ppn'])

pa = pyaudio.PyAudio()

audio_stream = pa.open(
   rate=porcupine.sample_rate,
   channels=1,
   format=pyaudio.paInt16,
   input=True,
   frames_per_buffer=porcupine.frame_length,
   input_device_index=None  # Use default input device
)

frame_count = 0
alive = True


while alive == True:
      
     pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
     pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
     keyword_detection = porcupine.process(pcm)
      
      
     if keyword_detection >= 0:
          print("Hello Sir")
          alive = False
          
          


if audio_stream:
     audio_stream.stop_stream()
     audio_stream.close()
if pa:
     pa.terminate()
if porcupine:
     porcupine.delete()
         
