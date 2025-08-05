import numpy as np
import wave

def generate_quiet_static_wav(output_path, duration_seconds=60, sample_rate=44100, noise_level=0.01):
    try:
        # Calculate number of samples
        num_samples = int(duration_seconds * sample_rate)
        
        # Generate white noise
        noise = np.random.normal(0, 1, num_samples)
        
        # Scale noise to very low amplitude (e.g., 1% of max int16 amplitude)
        max_amplitude = np.iinfo(np.int16).max
        quiet_noise = noise * noise_level * max_amplitude
        
        # Convert to int16 for WAV file
        quiet_noise = quiet_noise.astype(np.int16)
        
        # Save to WAV file
        with wave.open(output_path, "wb") as wf:
            wf.setframerate(sample_rate)
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.writeframes(quiet_noise)
            


        
        print(f"Generated quiet static WAV file at {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

generate_quiet_static_wav("quiet_static.wav", duration_seconds=2, noise_level=0.001)