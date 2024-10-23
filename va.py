import os
import pyaudio
import wave
import speech_recognition as sr
from google.cloud import dialogflow_v2 as dialogflow
from google.protobuf.json_format import MessageToDict
from gtts import gTTS
from IPython.display import Audio, display
from pydub import AudioSegment
import threading
import keyboard  
import time
from playsound import playsound


# Define the parameters for recording
FORMAT = pyaudio.paInt16  # Format for audio
CHANNELS = 1               # Number of audio channels
RATE = 44100               # Sample rate
CHUNK = 1024               # Buffer size
OUTPUT_FILENAME = "output.mp3"  # Output file name in MP3 format
WAVE_OUTPUT_FILENAME = "user_response.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Step 1: Set Up Google Cloud Credentials
service_account_file = './voice-assistant-shop-a192a8f1a614.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_file

# Global variable to track if the delivery address has been confirmed
address_confirmed = False
delivery_method = "Null"
stop_recording = False
exit = False


# Verify service account file
def check_service_account_file():
    if os.path.exists(service_account_file):
        print("Service account file found.")
    else:
        print("Service account file not found.")

# Step 2: Initialize the Dialogflow Client
project_id = 'voice-assistant-shop'
session_id = '123456'
language_code = 'en'
session_client = dialogflow.SessionsClient()
session_path = session_client.session_path(project_id, session_id)

# Step 3: Fast food item array and dynamic order array
fast_food_items = [
    {"name": "pizza", "description": "Delicious cheese pizza", "price": 8.99},
    {"name": "burger", "description": "Juicy beef burger", "price": 6.49},
    {"name": "fries", "description": "Crispy french fries", "price": 2.99},
]
order_list = []

# Convert OGG to WAV
def convert_ogg_to_wav(ogg_file):
    wav_file = ogg_file.replace('.ogg', '.wav')
    audio = AudioSegment.from_ogg(ogg_file)
    audio.export(wav_file, format="wav")
    return wav_file

# Step 4: Speech Recognition Function
def recognize_speech_from_file(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
        print("Recognizing...")
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            text = "Sorry, I could not understand the audio."
            return text
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None

# Detect Intent (only detects intent, other tasks are delegated)
def detect_intent_texts(text):
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session_path, query_input=query_input)
    print("Response = ", response)

    response_dict = MessageToDict(response._pb)
    intent_display_name = response_dict.get("queryResult", {}).get("intent", {}).get("displayName", "")
    print("Detected Intent = ", intent_display_name)

    if intent_display_name == "OrderIntent":
        return handle_order_intent(response_dict)
    elif intent_display_name == "CompleteOrderIntent":
        return handle_complete_order()
    elif intent_display_name == "ExitConversationIntent":
        return handle_exit_conversation()
    elif intent_display_name == "CheckProductAvailability":
        return handle_check_product_availability(response_dict)
    elif intent_display_name == "DeliverPickup":
        return handle_deliver_pickup_intent(response_dict)
    elif intent_display_name == "DeliveryAddress":
        return handle_delivery_address_intent(response_dict)
    elif intent_display_name == "AddressConfirmation":
        return handle_address_confirmation_intent(response_dict)
    else:
        return handle_fallback_response(text)

def handle_deliver_pickup_intent(response_dict):
    global delivery_method
    delivery_method = response_dict.get("queryResult", {}).get("parameters", {}).get("getorder", "")

    if delivery_method.lower() in ["delivery", "pickup"]:
        order_list.append({"delivery_method": delivery_method})
        response_text = (f"You have chosen {delivery_method}. "
                         f"{'Please provide your delivery address.' if delivery_method == 'delivery' else 'Thank You!'}")
    else:
        response_text = "Would you like your order for delivery or pickup?"

    print("Deliver/Pickup Response: ", response_text)
    return response_text

def handle_delivery_address_intent(response_dict):
    global address_confirmed  # Use the global variable to track address confirmation
    address = response_dict.get("queryResult", {}).get("parameters", {}).get("any", "")

    if address:
        if not address_confirmed:
            # Add the address to the order list
            order_list.append({"delivery_address": address})
            response_text = f"Thank you! We have noted your delivery address as: {address}. Is this correct? Please respond with yes or no."
        else:
            # If the address is confirmed
            response_text = "Thank you! Your delivery address is confirmed. Is there anything else you'd like to add?"
    else:
        response_text = "Could you please provide your delivery address?"

    print("Delivery Address Response: ", response_text)
    return response_text

def handle_address_confirmation_intent(response_dict):
    global address_confirmed
    user_response = response_dict.get("queryResult", {}).get("parameters", {}).get("confirmation", [])

    # Check if the response is a list and extract the first element
    if isinstance(user_response, list) and user_response:
        user_response = user_response[0].lower()  # Convert to lower case for case-insensitive matching
    else:
        user_response = ""  # Default to empty if there's no response

    print("Address confirmation user response = ", user_response)

    if user_response in ["yes", "y", "yeah"]:
        address_confirmed = True
        response_text = "Great! Your delivery address has been confirmed."
    elif user_response in ["no", "n", "nope"]:
        address_confirmed = False
        response_text = "I'm sorry! Could you please provide your delivery address again?"
    else:
        response_text = "I didn't quite catch that. Please respond with yes or no."

    print("Address Confirmation Response: ", response_text)
    return response_text

# Step 5: Handle Specific Intents
# Step 5: Handle Specific Intents
def handle_order_intent(response_dict):
    product_names, quantities, sizes = extract_order_details(response_dict)
    available_items, unavailable_items = process_order_items(product_names, quantities, sizes)

    response_text = format_order_response(available_items, unavailable_items)
    print("Response Text: ", response_text)
    return response_text

def handle_complete_order():
    # Check if the order list is not empty
    if not order_list:
        response_text = "You don't have any items in your order yet. Would you like to add something?"
        return response_text
    
    global delivery_method

    # Check if delivery method is specified
    delivery_method = next((item.get("delivery_method") for item in order_list if "delivery_method" in item), None)

    if not delivery_method:
        # Ask the user whether they want delivery or pickup
        response_text = "Would you like your order for delivery or pickup?"
        return response_text

    # If delivery method is 'delivery', check if the delivery address is provided
    if delivery_method == "delivery":
        delivery_address = next((item.get("delivery_address") for item in order_list if "delivery_address" in item), None)
        if not delivery_address:
            # Ask for the delivery address
            response_text = "Please provide your delivery address."
            return response_text

    # Calculate the total price of the order
    total_price = sum(item["quantity"] * item["price"] for item in order_list if "quantity" in item)
    delivery_address = next((item.get("delivery_address", "Not specified") for item in order_list if "delivery_address" in item), "Not specified")

    # Provide a summary of the order
    response_text = (f"Your order is complete. The total is ${total_price:.2f}. "
                    f"You have chosen: {delivery_method}. "
                    f"{'and your delivery address is ' + delivery_address + 'Kindly Select Payment method from the screen' if delivery_method == 'delivery' else 'Thank You!'}") 

    
    # Clear the order list for new orders
    order_list.clear()

    print("Complete Order Response: ", response_text)
    return response_text

def handle_check_product_availability(response_dict):
    # Extract the product names the user asked about
    product_names = [item.lower() for item in response_dict.get("queryResult", {}).get("parameters", {}).get("Product", [])]
    print("Product names = ", product_names)
    available_items = []
    unavailable_items = []

    # Check each product's availability
    for product_name in product_names:
        found_item = next((item for item in fast_food_items if item["name"].lower() == product_name), None)
        if found_item:
            available_items.append(found_item["name"])
        else:
            unavailable_items.append(product_name)

    # Prepare the response based on the available and unavailable products
    response_text = format_product_availability_response(available_items, unavailable_items)
    print("Product Availability Response: ", response_text)
    return response_text


# Format response for product availability
def format_product_availability_response(available_items, unavailable_items):
    response_text = ""

    if available_items:
        available_products = ', '.join(available_items)
        response_text += f"We have {available_products} available."

    if unavailable_items:
        unavailable_products = ', '.join(unavailable_items)
        if response_text:
            response_text += " However, "
        response_text += f"we don't have {unavailable_products}."

    if not available_items and not unavailable_items:
        response_text = "It seems like you didn't mention any valid products."

    return response_text

def handle_fallback_response(input_text):
    response_text = "Sorry, I didn't understand that. Could you please try again?"
    print("Fallback Response: ", response_text)
    return response_text

# Extract order details from the response
def extract_order_details(response_dict):
    product_names = [item.lower() for item in response_dict.get("queryResult", {}).get("parameters", {}).get("Product", [])]
    quantities = [int(number) for number in response_dict.get("queryResult", {}).get("parameters", {}).get("number", [])]
    sizes = [size.lower() for size in response_dict.get("queryResult", {}).get("parameters", {}).get("Size", [])]
    print(product_names, quantities, sizes)
    return product_names, quantities, sizes

def process_order_items(product_names, quantities, sizes):
    available_items = []
    unavailable_items = []

    for i, item_name in enumerate(product_names):
        found_item = next((item for item in fast_food_items if item["name"].lower() == item_name), None)
        if found_item:
            available_items.append(found_item)
            order_details = {
                "name": found_item["name"],
                "quantity": quantities[i] if i < len(quantities) else 1,
                "size": sizes[i] if i < len(sizes) else "regular",
                "price": found_item["price"]
            }
            order_list.append(order_details)
        else:
            unavailable_items.append(item_name)
    return available_items, unavailable_items

def format_order_response(available_items, unavailable_items):
    if available_items:
        available_products = ', '.join([f"{item['name']} " for item, order in zip(available_items, order_list)])
        response_text = f"Yes, we have {available_products} available. They have been added to your order. Would you like to add something else?"
    else:
        response_text = "Unfortunately, we don't have any of the items you requested."

    if unavailable_items:
        unavailable_products = ', '.join(unavailable_items)
        response_text += f" However, we don't have {unavailable_products}. Would you like to try something else?"

    return response_text

def speak_response(text):
    tts = gTTS(text=text, lang='en')
    tts.save("response.mp3")
    play_audio("response.mp3")

def play_audio(audio):
    print("Playing back recorded audio...")
    
    # Open the wave file
    wf = wave.open(audio, 'rb')
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with the wave file parameters
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read data in chunks and play
    data = wf.readframes(CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(CHUNK)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    
    # Terminate the PyAudio session
    p.terminate()

    # Close the wave file
    wf.close()

def speak_text(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    tts.save("response.mp3")
    display(Audio("response.mp3"))

# Step 7: Get Fulfillment Text for Other Intents
def get_fulfillment_text(text):
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session_path, query_input=query_input)
    return response.query_result.fulfillment_text

def record_audio_now():
    """ Record audio until the stop condition is met. """
    global stop_recording
    print("Recording... Press Enter to stop.")
    
    # Start recording
    record_audio(seconds=5)  # Use your existing record_audio function

    # After recording, check for recognized text
    recognized_text = recognize_speech_from_file(WAVE_OUTPUT_FILENAME)
    if recognized_text:
        print("You said: ", recognized_text)
    
    # Stop the recording process
    stop_recording = True

def listen_for_enter():
    """ Listen for the Enter key to stop recording. """
    global stop_recording
    keyboard.wait('enter')  # Wait for Enter key to be pressed
    stop_recording = True  # Set the stop condition

# Function to convert text to audio
def text_to_audio(text):
    tts = gTTS(text=text, lang='en')
    tts.save(OUTPUT_FILENAME)
    print(f"Text converted to audio and saved as {OUTPUT_FILENAME}")

    # Play the generated audio
    playsound(OUTPUT_FILENAME)

    # Optionally, remove the audio file after playback
    os.remove(OUTPUT_FILENAME)

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
    print("Recording Complete")

def handle_exit_conversation():
    response_text = "Thank you for visiting! If you need anything else, feel free to ask. Goodbye!"
    global exit
    exit = True
    print("Exit Conversation Response:", response_text)
    return response_text

# Main loop to interact with the user
def main():
    # Initial greeting
    greetings = get_fulfillment_text("Hi")
    print("Response = ", greetings)
    text_to_audio(greetings)

    print("I am hereeeee")

    # # Start recording in a separate thread
    # recording_thread = threading.Thread(target=record_audio_now)
    # recording_thread.start()

    # # Start listening for Enter key in the main thread
    # listen_for_enter()

    while True:
        record_audio(10)

        recognized_text = recognize_speech_from_file(WAVE_OUTPUT_FILENAME)
        if recognized_text:
            print("You said: ", recognized_text)
    
    # Wait for the recording thread to finish
    # recording_thread.join()

    # After stopping, process the recognized text (already done in record_audio)
    # The recognized text is processed within record_audio now.

    # Send recognized text to Dialogflow for intent detection
    # Process the recognized text if it's been captured.
        if recognized_text:
            response_text = detect_intent_texts(recognized_text)
            print("Response = ", response_text)
            print("I am here at the response")
            text_to_audio(response_text)
            print("My Order is", order_list)

        if exit:
            break

        if delivery_method == "pickup":
            complete_order_response = handle_complete_order()
            print("Complete Order Response: ", complete_order_response)
            text_to_audio(complete_order_response)
            text_to_audio("Select Payment Method from your screen")
            break

        # Check if the address is confirmed
        if address_confirmed:
            complete_order_response = handle_complete_order()
            print("Complete Order Response: ", complete_order_response)
            text_to_audio(complete_order_response)

        # If the response indicates the user wants to exit, handle it


    if "goodbye" in response_text.lower():
        print("Ending conversation.")

# Start the assistant
if __name__ == "__main__":
    check_service_account_file()
    main()