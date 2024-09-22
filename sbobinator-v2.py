import streamlit as st
from openai import OpenAI
import tempfile
import os
import yt_dlp
from pydub import AudioSegment
import math

st.set_page_config(layout="wide", page_title="Trascrittore Audio", page_icon="🎙️")

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB in bytes

# Function to validate OpenAI API key
@st.cache_data(show_spinner=False)
def is_valid_api_key(api_key):
    if not api_key:
        return False
    try:
        client = OpenAI(api_key=api_key)
        # Make a simple API call to check if the key is valid
        client.models.list()
        return True
    except Exception:
        return False

def download_youtube_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{info['id']}.mp3"
    return filename

def transcribe_audio_chunk(client, file_path, language):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language
        )
    return transcript.text

def process_large_audio(client, file_path, language):
    audio = AudioSegment.from_file(file_path)
    duration_ms = len(audio)
    chunk_duration_ms = math.ceil(CHUNK_SIZE / (audio.frame_width * audio.frame_rate / 1000))
    
    transcripts = []
    
    for i in range(0, duration_ms, chunk_duration_ms):
        chunk = audio[i:i+chunk_duration_ms]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            chunk.export(tmp_file.name, format="wav")
            transcript_chunk = transcribe_audio_chunk(client, tmp_file.name, language)
            transcripts.append(transcript_chunk)
        os.unlink(tmp_file.name)
    
    return " ".join(transcripts)

# Sidebar for API key input
st.sidebar.title("Configurazioni")
api_key = st.sidebar.text_input("Inserisci la tua API Key", type="password")

# Check API key validity
if api_key:
    if is_valid_api_key(api_key):
        st.sidebar.success("API Key valida!")
    else:
        st.sidebar.error("API Key non valida. Ricontrolla e riprova.")

st.title("Trascrittore Audio")

# Input options
input_option = st.radio("Scegli il tipo di input:", ("File audio", "URL YouTube"))

if input_option == "File audio":
    uploaded_file = st.file_uploader("Carica un file audio", type=["mp3", "wav", "ogg"])
    if uploaded_file is not None:
        st.audio(uploaded_file)
        file_size = uploaded_file.size
        st.write(f"Dimensione del file: {file_size / 1024 / 1024:.2f} MB")
else:
    youtube_url = st.text_input("Inserisci l'URL del video YouTube")

languages = {
    "Italiano": "it",
    "English": "en",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es"
}
selected_language = st.selectbox("Seleziona la lingua dell'audio", list(languages.keys()))

if st.button("Trascrivi"):
    if not api_key or not is_valid_api_key(api_key):
        st.error("Inserisci una API Key valida nella barra laterale.")
    else:
        try:
            client = OpenAI(api_key=api_key)

            if input_option == "File audio" and uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split('.')[-1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
            elif input_option == "URL YouTube" and youtube_url:
                tmp_file_path = download_youtube_audio(youtube_url)
            else:
                st.error("Carica un file audio o inserisci un URL YouTube valido.")
                st.stop()

            with st.spinner("Sto trascrivendo..."):
                file_size = os.path.getsize(tmp_file_path)
                if file_size > MAX_FILE_SIZE:
                    st.warning(f"Il file supera il limite di {MAX_FILE_SIZE / 1024 / 1024} MB. Verrà elaborato in chunks.")
                    transcript_text = process_large_audio(client, tmp_file_path, languages[selected_language])
                else:
                    transcript_text = transcribe_audio_chunk(client, tmp_file_path, languages[selected_language])

            st.subheader("Trascrizione:")
            st.write(transcript_text)
            
            word_count = len(transcript_text.split())
            st.info(f"Numero di parole: {word_count}")

            st.download_button(
                label="Scarica trascrizione",
                data=transcript_text,
                file_name="trascrizione.txt",
                mime="text/plain"
            )

            os.unlink(tmp_file_path)
        except Exception as e:
            st.error(f"Si è verificato un errore: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit e OpenAI")