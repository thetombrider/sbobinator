import streamlit as st
from openai import OpenAI
import assemblyai as aai
import tempfile
import os
import yt_dlp
import requests
import re

st.set_page_config(layout="wide", page_title="Trascrittore Audio", page_icon="🎙️")

# Function to validate OpenAI API key
@st.cache_data(show_spinner=False)
def is_valid_openai_api_key(api_key):
    if not api_key:
        return False
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return True
    except Exception:
        return False

# Function to validate AssemblyAI API key
@st.cache_data(show_spinner=False)
def is_valid_assemblyai_api_key(api_key):
    if not api_key:
        return False
    try:
        headers = {"authorization": api_key}
        response = requests.get("https://api.assemblyai.com/v2/account", headers=headers)
        return response.status_code == 200
    except Exception:
        return False

# Function to validate YouTube URL
def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(youtube_regex, url)
    return bool(match)

@st.cache_data(show_spinner=False)
def download_youtube_audio(youtube_url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
                
            # Find the downloaded file
            files = os.listdir(temp_dir)
            if not files:
                raise ValueError("Nessun file audio scaricato")
            
            file_name = files[0]
            file_path = os.path.join(temp_dir, file_name)
            
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
        
        return audio_data, file_name
    except Exception as e:
        raise Exception(f"Errore nel download dell'audio: {str(e)}")

# Sidebar for API key inputs and dashboard links
st.sidebar.title("Inserisci le tue API Keys")

# OpenAI section
st.sidebar.subheader("OpenAI")
openai_api_key = st.sidebar.text_input("Inserisci la tua API Key di OpenAI", type="password")
st.sidebar.markdown("[Dashboard OpenAI](https://platform.openai.com/account/api-keys)")

# Check OpenAI API key validity
if openai_api_key:
    if is_valid_openai_api_key(openai_api_key):
        st.sidebar.success("API Key di OpenAI valida!")
    else:
        st.sidebar.error("API Key di OpenAI non valida. Ricontrolla e riprova.")

st.sidebar.markdown("---")

# AssemblyAI section
st.sidebar.subheader("AssemblyAI")
assemblyai_api_key = st.sidebar.text_input("Inserisci la tua API Key di AssemblyAI", type="password")
st.sidebar.markdown("[Dashboard AssemblyAI](https://www.assemblyai.com/app/account)")

# Check AssemblyAI API key validity
if assemblyai_api_key:
    if is_valid_assemblyai_api_key(assemblyai_api_key):
        st.sidebar.success("API Key di AssemblyAI valida!")
    else:
        st.sidebar.error("API Key di AssemblyAI non valida. Ricontrolla e riprova.")

st.title("Sbobinator")
st.subheader("Il tuo assistente per le trascrizioni audio")

# Input options
input_option = st.radio("Scegli il tipo di input:", ("File audio", "URL YouTube"))

audio_source = None
file_name = None

if input_option == "File audio":
    uploaded_file = st.file_uploader("Carica un file audio", type=["mp3", "wav", "ogg", "mp4", "m4a", "flac"])
    if uploaded_file is not None:
        audio_source = {"type": "local", "data": uploaded_file.getvalue()}
        st.audio(uploaded_file)
        file_name = uploaded_file.name

elif input_option == "URL YouTube":
    youtube_url = st.text_input("Inserisci l'URL del video YouTube")
    if youtube_url:
        if is_valid_youtube_url(youtube_url):
            try:
                with st.spinner("Sto scaricando l'audio dal video YouTube..."):
                    audio_data, file_name = download_youtube_audio(youtube_url)
                audio_source = {"type": "local", "data": audio_data}
                st.audio(audio_data)
            except Exception as e:
                st.error(str(e))
        else:
            st.error("URL YouTube non valido. Inserisci un URL valido.")

if audio_source:
    # Transcription options
    transcription_option = st.selectbox(
        "Seleziona il tipo di trascrizione",
        ["Senza diarizzazione (OpenAI)", "Con diarizzazione (AssemblyAI)"]
    )
    st.markdown("""
    <small>
    <i>Nota: La diarizzazione è il processo di separazione degli speaker in una conversazione. 
    Attivala se l'audio contiene più voci e desideri distinguere chi sta parlando. 
    Considera che la diarizzazione non è supportata da OpenAI, quindi l'applicazione utilizzerà AssemblyAI, che ha un costo di trascrizione maggiore.
    </i>
    </small>
    """, unsafe_allow_html=True)

    # Language selection (for both OpenAI and AssemblyAI)
    languages = {
        "Italiano": "it",
        "English": "en",
        "Français": "fr",
        "Deutsch": "de",
        "Español": "es"
    }
    selected_language = st.selectbox("Seleziona la lingua dell'audio", list(languages.keys()))

    if st.button("Trascrivi"):
        if transcription_option == "Senza diarizzazione (OpenAI)":
            if not openai_api_key or not is_valid_openai_api_key(openai_api_key):
                st.error("Inserisci una API Key valida di OpenAI nella barra laterale.")
            else:
                try:
                    client = OpenAI(api_key=openai_api_key)

                    with tempfile.NamedTemporaryFile(delete=False, suffix="." + file_name.split('.')[-1]) as tmp_file:
                        tmp_file.write(audio_source["data"])
                        tmp_file_path = tmp_file.name

                    with st.spinner("Sto trascrivendo..."):
                        with open(tmp_file_path, "rb") as audio_file:
                            transcript = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                language=languages[selected_language]
                            )

                    st.subheader("Trascrizione:")
                    st.write(transcript.text)

                    st.download_button(
                        label="Scarica trascrizione",
                        data=transcript.text,
                        file_name="trascrizione.txt",
                        mime="text/plain"
                    )

                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")
        else:  # With diarization (AssemblyAI)
            if not assemblyai_api_key or not is_valid_assemblyai_api_key(assemblyai_api_key):
                st.error("Inserisci una API Key valida di AssemblyAI nella barra laterale.")
            else:
                try:
                    aai.settings.api_key = assemblyai_api_key
                    transcriber = aai.Transcriber()

                    with tempfile.NamedTemporaryFile(delete=False, suffix="." + file_name.split('.')[-1]) as tmp_file:
                        tmp_file.write(audio_source["data"])
                        tmp_file_path = tmp_file.name

                    with st.spinner("Sto trascrivendo con diarizzazione..."):
                        transcript = transcriber.transcribe(
                            tmp_file_path,
                            config=aai.TranscriptionConfig(
                                speaker_labels=True,
                                language_code=languages[selected_language]
                            )
                        )

                    st.subheader("Trascrizione con diarizzazione:")
                    for utterance in transcript.utterances:
                        st.write(f"Speaker {utterance.speaker}: {utterance.text}")

                    # Prepare the full transcript text with speaker labels
                    full_transcript = "\n".join([f"Speaker {u.speaker}: {u.text}" for u in transcript.utterances])

                    st.download_button(
                        label="Scarica trascrizione",
                        data=full_transcript,
                        file_name="trascrizione_con_diarizzazione.txt",
                        mime="text/plain"
                    )

                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")
else:
    st.info("Carica un file audio o inserisci un URL YouTube per iniziare.")

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit, OpenAI e AssemblyAI")

