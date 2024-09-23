import streamlit as st
import re
import tempfile
import os
import yt_dlp
import gdown
import requests
from openai import OpenAI
import assemblyai as aai

languages = {
    "Italiano": "it",
    "English": "en",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es"
}

# Function to validate YouTube URL
def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(youtube_regex, url)
    return bool(match)

# Function to validate and extract Google Drive file ID
def extract_google_drive_file_id(url):
    patterns = [
        r'https://drive\.google\.com/file/d/([\w-]+)(?:/.*)?',
        r'https://drive\.google\.com/open\?id=([\w-]+)',
        r'https://drive\.google\.com/uc\?id=([\w-]+)',
        r'https://drive\.google\.com/file/d/([\w-]+)/view\?usp=sharing'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Function to download file from Google Drive
@st.cache_data(show_spinner=False)
def download_file_from_google_drive(url):
    try:
        file_id = extract_google_drive_file_id(url)
        if not file_id:
            raise ValueError("Invalid Google Drive URL")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
            temp_path = temp_file.name
            gdown.download(id=file_id, output=temp_path, quiet=False)

            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise Exception("Download failed or file is empty")

            with open(temp_path, 'rb') as file:
                file_content = file.read()

            file_name = os.path.basename(gdown.download(id=file_id, output=None, quiet=True))

        return file_content, file_name
    except Exception as e:
        raise Exception(f"Error downloading from Google Drive: {str(e)}")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

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
            'outtmpl': '%(title)s.%(ext)s',
            # Rimuovi l'opzione cookiesfrombrowser
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            # Aggiungi queste opzioni per aggirare alcune restrizioni
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
            'geo_bypass': True,
            'geo_bypass_country': 'IT'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                file_name = ydl.prepare_filename(info)
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

def download_audio_from_url(url):
    response = requests.get(url)
    file_name = url.split("/")[-1]
    return response.content, file_name

def summarize_transcript(api_key, transcript, language):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Summarize the following transcript in {language}. 
    Focus on the main topics discussed, key points made, and any important conclusions or decisions reached.
    If the transcript includes multiple speakers, try to capture the essence of their contributions without necessarily attributing specific points to individuals.
    Aim for a concise yet comprehensive summary that gives a clear overview of the content.
    If there are any standout quotes or particularly important moments, include those.
    
    Transcript:
    {transcript}
    
    Summary:"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled assistant specializing in summarizing transcripts. Your summaries are clear, concise, and capture the essence of the discussion."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300  # Increased token limit for a more detailed summary
    )
    
    return response.choices[0].message.content.strip()

def add_sidebar_content():
    st.sidebar.title("API Dashboards")
    st.sidebar.markdown("[OpenAI Dashboard](https://platform.openai.com/)")
    st.sidebar.markdown("[AssemblyAI Dashboard](https://www.assemblyai.com/dashboard)")

def transcribe_with_openai(audio_data, api_key):
    client = OpenAI(api_key=api_key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio.flush()
        
        with open(temp_audio.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
    
    os.unlink(temp_audio.name)
    return transcript

def transcribe_with_assemblyai(audio_data, api_key, language):
    aai.settings.api_key = api_key
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio.flush()
        
        config = aai.TranscriptionConfig(speaker_labels=True, language_code=language)
        transcript = aai.Transcriber().transcribe(temp_audio.name, config=config)
    
    os.unlink(temp_audio.name)
    return transcript

def send_email(to_email, subject, body):
    if "resend_api_key" not in st.secrets or not st.secrets["resend_api_key"]:
        st.error("La Resend API Key non è configurata nei secrets.")
        return None, "Resend API Key mancante."
    resend_api_key = st.secrets["resend_api_key"]

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "from": "sbobinator@minutohomeserver.xyz",  # Assicurati di utilizzare un indirizzo 'from' verificato
        "to": [to_email],
        "subject": subject,
        "html": body
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        error_status = e.response.status_code if e.response else None
        error_response = e.response.text if e.response else str(e)
        st.error(f"Errore nell'invio dell'email: {error_response}")
        return error_status, error_response

def perform_transcription(audio_source, transcription_option, api_keys, selected_language):
    full_transcript = ""
    
    try:
        with st.spinner("Sto trascrivendo..."):
            if transcription_option == "Senza diarizzazione (OpenAI)":
                transcript = transcribe_with_openai(audio_source["data"], api_keys["openai"])
                full_transcript = transcript.text
            else:
                transcript = transcribe_with_assemblyai(
                    audio_source["data"],
                    api_keys["assemblyai"],
                    languages[selected_language]
                )
                full_transcript = "\n".join([
                    f"Speaker {utterance.speaker}: {utterance.text}"
                    for utterance in transcript.utterances
                ])
    except Exception as e:
        st.error(f"Si è verificato un errore durante la trascrizione: {str(e)}")
    
    return full_transcript, summary