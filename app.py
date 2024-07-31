import os
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
from gtts import gTTS
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import subprocess

from google.cloud import texttospeech
import json
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account

# Load environment variables
# load_dotenv()


GOOGLE_API_KEY = st.secrets["API_KEY"]

#credentials = Credentials.from_service_account_file(
#    'avian-serenity-427813-m3-70c98e1468ee.json')

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["client_ts"]
)

client = texttospeech.TextToSpeechClient(credentials=credentials)

# Set up Google Gemini-Pro AI model
genai.configure(api_key=GOOGLE_API_KEY)

# Load gemini-1.5 Flash vision model


def gemini_1_5_flash():
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

# Get response from gemini pro vision model


def gemini_vision_response(model, prompt, image):
    response = model.generate_content([prompt, image])
    return response.text

# Convert text to audio using gtts


def text_to_audio(text, filename="response.mp3"):
    tts = gTTS(text)
    tts.save(filename)
    return filename

# Function to convert audio to text (provided by the user)


def audio_to_text(audio_file):
    # Placeholder for the actual function implementation
    # This function should return the transcribed text from the audio file
    pass


# Set page title and icon
st.set_page_config(
    page_title="SpeakSpark",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# with st.sidebar:
#     user_picked = option_menu(
#         "Language Bot",
#         ["ChatBot", "Image Captioning"],
#         menu_icon="robot",
#         icons=["chat-dots-fill", "image-fill"],
#         default_index=0
#     )


def roleForStreamlit(user_role):
    if user_role == 'model':
        return 'assistant'
    else:
        return user_role


def transcribe_audio():

    command = ["whisper", "mic_rec.mp3",
               "--language", "English", "--fp16", "False"]

    try:
        result = subprocess.run(command, check=True,
                                capture_output=True, text=True)
        print("Command output:")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("An error occurred while running the command:")
        print(e.stderr)
        return 'Sorry there was an error somewhere. Could you repeat?'


def get_user_input(audio_data):

    if audio_data is not None:

        # if i < 1:
        st.audio(audio_data["bytes"], format="audio/mp3")
        # i += 1

    # Download button for recorded audio
        with open("mic_rec.mp3", "wb") as f:
            f.write(audio_data["bytes"])

        transcript = transcribe_audio()
        # transcript_holder = st.empty()

        # with open("mic_rec.txt") as my_file:
        #     # print(my_file.read())

        #     x = my_file.read()

        #     # st.subheader(f"Transcript: {x}")

        #     return x
        return transcript


system_prompt = """You are a friendly English conversation partner designed to help users improve their English skills. Your primary goals are:

1. Engage in casual, natural conversations on various topics.
2. Discreetly identify and correct grammatical errors made by the user.
3. Your tone must be a bit informal, such that the user is having conversations with their friends. 
4. Provide gentle, constructive feedback on language use.
5. You must detect grammatical errors in the input of the user, and nicely correct it while responding to them. 

When interacting:
- Maintain a warm and encouraging tone.
- If you notice a grammatical error, politely point it out and provide the correct form.
- After correcting an error, smoothly continue the conversation.
- Use language appropriate for intermediate English learners.
- Never use Emojis or Emoticons. 
- Occasionally introduce new vocabulary or idioms, explaining them in simple terms.

Remember, your main purpose is to help users practice and improve their English in a comfortable, conversational setting."""


def roleForStreamlit(user_role):
    if user_role == 'model':
        return 'assistant'
    else:
        return user_role


i = 0


model = gemini_1_5_flash()

if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = model.start_chat(history=[
        {
            "role": "model",
            "parts": [{"text": system_prompt}]
        }
    ])

st.title("SpeakSpark")

# Display the chat history if it's not empty
if st.session_state.chat_history.history:
    for message in st.session_state.chat_history.history:
        with st.chat_message(roleForStreamlit(message.role)):

            if i == 0:
                i += 1
            else:
                st.markdown(message.parts[0].text)

            print(message.parts[0].text)

# Record audio input
audio_data = mic_recorder()
if audio_data:
    # Convert audio to text
    # user_input = audio_to_text(audio_data)

    user_input = get_user_input(audio_data)

    # user_input = 'user_input'
    # Continue the chat with transcribed text
    st.chat_message("user").markdown(f'{user_input}')
    response = st.session_state.chat_history.send_message(user_input)

    # Convert response text to audio and play it
    # audio_file = text_to_audio(response.text)

    synthesis_input = texttospeech.SynthesisInput(text=response.text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name='en-US-Wavenet-F'
    )

    # en-US-Journey-F
    # en-US-Wavenet-F

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,

        speaking_rate=1,
        pitch=1
    )

    audio_response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # audio_bytes = open(audio_response.audio_content, "rb").read()
    st.audio(audio_response.audio_content)
