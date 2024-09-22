import streamlit as st
from openai import OpenAI
import assemblyai as aai
import tempfile
import os
import yt_dlp
import requests
import re

st.set_page_config(layout="wide", page_title="Sbobinator", page_icon="🎙️")

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

# Function to validate and extract Google Drive file ID
def extract_google_drive_file_id(url):
    patterns = [
        r'https://drive\.google\.com/file/d/([\w-]+)',
        r'https://drive\.google\.com/open\?id=([\w-]+)',
        r'https://drive\.google\.com/uc\?id=([\w-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Function to download file from Google Drive
def download_file_from_google_drive(file_id):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    return response.content

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

# Modified function to handle both YouTube and Google Drive URLs
@st.cache_data(show_spinner=False)
def download_audio_from_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        # YouTube URL handling (keep existing YouTube download logic)
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
                    ydl.download([url])
                    
                files = os.listdir(temp_dir)
                if not files:
                    raise ValueError("Nessun file audio scaricato")
                
                file_name = files[0]
                file_path = os.path.join(temp_dir, file_name)
                
                with open(file_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
            
            return audio_data, file_name
        except Exception as e:
            raise Exception(f"Errore nel download dell'audio da YouTube: {str(e)}")
    else:
        # Google Drive URL handling
        file_id = extract_google_drive_file_id(url)
        if file_id:
            try:
                file_content = download_file_from_google_drive(file_id)
                file_name = f"google_drive_audio_{file_id}.mp3"  # Default name, might not be accurate
                return file_content, file_name
            except Exception as e:
                raise Exception(f"Errore nel download dell'audio da Google Drive: {str(e)}")
        else:
            raise ValueError("URL non valido. Inserisci un URL valido di YouTube o Google Drive.")

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

# Modified input options
input_option = st.radio("Scegli il tipo di input:", ("File audio", "URL (YouTube o Google Drive)"))

audio_source = None
file_name = None

if input_option == "File audio":
    uploaded_file = st.file_uploader("Carica un file audio", type=["mp3", "wav", "ogg", "mp4", "m4a", "flac"])
    if uploaded_file is not None:
        audio_source = {"type": "local", "data": uploaded_file.getvalue()}
        st.audio(uploaded_file)
        file_name = uploaded_file.name

elif input_option == "URL (YouTube o Google Drive)":
    url = st.text_input("Inserisci l'URL del video YouTube o del file audio su Google Drive")
    if url:
        try:
            with st.spinner("Sto scaricando l'audio dall'URL..."):
                audio_data, file_name = download_audio_from_url(url)
            audio_source = {"type": "local", "data": audio_data}
            st.audio(audio_data)
        except Exception as e:
            st.error(str(e))

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
    st.info("Carica un file audio o inserisci un URL YouTube o Google Drive per iniziare.")

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit, OpenAI e AssemblyAI")

