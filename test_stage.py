import pvporcupine
import pyaudio
import struct

def test_porcupine():
    porcupine = None
    pa = None
    audio_stream = None
    
    try:
        print("Setting up Porcupine...")
        
        # Initialize Porcupine with built-in wake words
        porcupine = pvporcupine.create(
            access_key = "QDvMT9ImmgTsLR7E7793aAhHR6PVHQh4C8c/PBOlsewNqIJRuoUxcg==",
            keyword_paths=['/home/freddy-berg/CARL/wake_files/hey-carl.ppn']
        )
        
        
        print(f"Porcupine initialized successfully!")
        print(f"Sample rate: {porcupine.sample_rate}")
        print(f"Frame length: {porcupine.frame_length}")
        
        # Audio stream configuration
        pa = pyaudio.PyAudio()
        
        # Check available audio devices
        print("\nAvailable audio devices:")
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']}")
        
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=None  # Use default input device
        )
        
        print("\n🎤 Listening for 'picovoice' wake word... (Press Ctrl+C to stop)")
        print("Try saying 'picovoice' clearly...")
        
        frame_count = 0
        while True:
            try:
                # Read audio frame
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                
                # Process the audio frame
                keyword_index = porcupine.process(pcm)
                
                frame_count += 1
                if frame_count % 100 == 0:  # Print every 100 frames (~3 seconds)
                    print(".", end="", flush=True)
                
                # Check if wake word was detected
                if keyword_index >= 0:
                    print(f"\n🚨 WAKE WORD DETECTED! Index: {keyword_index}")
                    print("Wake word 'picovoice' was heard!")
                    
            except Exception as e:
                print(f"Error reading audio: {e}")
                break
                
    except Exception as e:
        print(f"Error: {e}")
        print("\nCommon issues:")
        print("1. Invalid access key - get one from https://console.picovoice.ai/")
        print("2. No microphone access - check permissions")
        print("3. Missing dependencies - install with 'pip install pvporcupine pyaudio'")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
        
    finally:
        # Clean up resources
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if pa:
            pa.terminate()
        if porcupine:
            porcupine.delete()
        print("Cleanup complete.")

# Test basic functionality first
def test_basic_setup():
    print("Testing basic Porcupine setup...")
    try:
        # Test without audio
        porcupine = pvporcupine.create(
            access_key='QDvMT9ImmgTsLR7E7793aAhHR6PVHQh4C8c/PBOlsewNqIJRuoUxcg==',
            keywords=['picovoice']
        )
        print("✅ Porcupine created successfully!")
        porcupine.delete()
        return True
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    print("Porcupine Wake Word Detection Test\n")
    
    # First test basic setup
    if test_basic_setup():
        print("\nStarting audio detection...")
        test_porcupine()
    else:
        print("Please fix the setup issues before proceeding.")