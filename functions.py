import streamlit as st
import re
import tempfile
import os
import yt_dlp
import gdown
import requests
import mimetypes
from openai import OpenAI

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

def download_audio_from_url(url):
    response = requests.get(url)
    file_name = url.split("/")[-1]
    return response.content, file_name

def summarize_transcript(api_key, transcript, language):
    client = OpenAI(api_key=api_key)
    
    prompt = f"Summarize the following transcript in {language}:\n\n{transcript}\n\nSummary:"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes transcripts."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()