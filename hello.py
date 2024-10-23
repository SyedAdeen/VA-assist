from gtts import gTTS
from playsound import playsound
import os

# Define output file name
OUTPUT_FILENAME = "output.mp3"  # Output file name in MP3 format

# Function to convert text to audio
def text_to_audio(text):
    tts = gTTS(text=text, lang='en')
    tts.save(OUTPUT_FILENAME)
    print(f"Text converted to audio and saved as {OUTPUT_FILENAME}")

# Input text from user
text = input("Enter the text you want to convert to audio: ")

# Convert text to audio
text_to_audio(text)

# Play the generated audio
playsound(OUTPUT_FILENAME)

# Optionally, remove the audio file after playback
os.remove(OUTPUT_FILENAME)
