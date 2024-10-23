# import pyaudio
# import wave

# # Define the parameters for recording
# FORMAT = pyaudio.paInt16  # Format for audio
# CHANNELS = 1               # Number of audio channels
# RATE = 44100               # Sample rate
# CHUNK = 1024               # Buffer size
# WAVE_OUTPUT_FILENAME = "output.wav"  # Output file name

# # Initialize PyAudio
# audio = pyaudio.PyAudio()

# # Function to record audio
# def record_audio(seconds):
#     print("Recording...")
#     stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

#     frames = []
#     for _ in range(0, int(RATE / CHUNK * seconds)):
#         data = stream.read(CHUNK)
#         frames.append(data)

#     print("Done recording.")
    
#     # Stop and close the stream
#     stream.stop_stream()
#     stream.close()

#     # Save the recorded data as a .wav file
#     with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(audio.get_sample_size(FORMAT))
#         wf.setframerate(RATE)
#         wf.writeframes(b''.join(frames))

# # Function to play audio
# def play_audio():
#     print("Playing back recorded audio...")
#     wf = wave.open(WAVE_OUTPUT_FILENAME, 'rb')
#     stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
#                         channels=wf.getnchannels(),
#                         rate=wf.getframerate(),
#                         output=True)

#     data = wf.readframes(CHUNK)
#     while data:
#         stream.write(data)
#         data = wf.readframes(CHUNK)

#     stream.stop_stream()
#     stream.close()

# # Record audio for 5 seconds
# record_audio(5)

# # Play the recorded audio
# play_audio()

# # Terminate the PyAudio session
# audio.terminate()




import pyaudio
import wave

# Define the parameters for recording
FORMAT = pyaudio.paInt16  # Format for audio
CHANNELS = 1               # Number of audio channels
RATE = 44100               # Sample rate
CHUNK = 1024               # Buffer size
WAVE_OUTPUT_FILENAME = "output.wav"  # Output file name

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Function to record audio
def record_audio(seconds):
    print("Recording...")
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Done recording.")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Save the recorded data as a .wav file
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

# Function to play audio
def play_audio():
    print("Playing back recorded audio...")
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'rb')
    stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

    data = wf.readframes(CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

# Record audio for 5 seconds
record_audio(5)

# Play the recorded audio
play_audio()

# Terminate the PyAudio session
audio.terminate()
