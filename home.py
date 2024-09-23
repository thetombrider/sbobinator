import streamlit as st
from openai import OpenAI
import assemblyai as aai
import tempfile
import requests
import os
import io
import mimetypes
from pages.config import app as config_page, load_api_keys, is_valid_openai_api_key, is_valid_assemblyai_api_key
from functions import (
    is_valid_youtube_url,
    extract_google_drive_file_id,
    download_file_from_google_drive,
    download_youtube_audio,
    download_audio_from_url,
    summarize_transcript,
    add_sidebar_content,
    send_email,
    transcribe_with_openai,
    transcribe_with_assemblyai,
    perform_transcription,
    languages
)

# Add this at the very beginning of your file
st.set_page_config(
    page_title="Sbobinator",
    page_icon="🎙️",
    menu_items={
        'About': """
        # Sbobinator

        Sbobinator è un'applicazione web avanzata per la trascrizione e il riassunto di file audio, 
        utilizzando tecnologie all'avanguardia come OpenAI Whisper e AssemblyAI.

        ## Caratteristiche principali:
        - Trascrizione di file audio caricati localmente
        - Supporto per l'elaborazione di audio da URL di YouTube e Google Drive
        - Opzione di trascrizione con o senza diarizzazione (separazione degli speaker)
        - Generazione automatica di riassunti delle trascrizioni
        - Supporto multilingua

        Creato da Tommaso Minuto

        Versione: 0.1
        """
    }
)

# Add sidebar content
add_sidebar_content()

st.title("Sbobinator")

# Move the info message to the top
st.info("Carica un file audio o inserisci un URL YouTube o Google Drive per iniziare.")

# Check API keys and show alerts
api_keys = load_api_keys()
if is_valid_openai_api_key(api_keys["openai"]) and is_valid_assemblyai_api_key(api_keys["assemblyai"]):
    st.success("Le API keys sono state caricate correttamente.")
else:
    st.warning("Le API keys non sono valide o mancanti. Per favore, inseriscile nella pagina di configurazione.")

# Input options
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
                if is_valid_youtube_url(url):
                    audio_data, file_name = download_youtube_audio(url)
                elif extract_google_drive_file_id(url):
                    audio_data, file_name = download_file_from_google_drive(url)
                else:
                    audio_data, file_name = download_audio_from_url(url)
                
                if not audio_data:
                    raise ValueError("No audio data downloaded")

                audio_source = {"type": "local", "data": audio_data}
                
                # Determine the MIME type based on the file extension
                mime_type, _ = mimetypes.guess_type(file_name)
                if mime_type is None:
                    mime_type = 'audio/wav' if file_name.lower().endswith('.wav') else 'audio/mp3'
                
                st.audio(io.BytesIO(audio_data), format=mime_type)
                st.success(f"File scaricato con successo: {file_name}")

                # Debug information
                st.write(f"File size: {len(audio_data) / (1024 * 1024):.2f} MB")
                #st.write(f"MIME type: {mime_type}")
        except Exception as e:
            st.error(f"Si è verificato un errore durante il download o l'elaborazione dell'audio: {str(e)}")
            st.info("Se il problema persiste con i video di YouTube, prova a utilizzare un URL diverso o a caricare direttamente un file audio.")

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
        if not api_keys["openai"] or not api_keys["assemblyai"]:
            st.error("Le API keys non sono valide o mancanti. Per favore, inseriscile nella pagina di configurazione.")
        else:
            full_transcript, summary = perform_transcription(audio_source, transcription_option, api_keys, selected_language)
            
            # Display the transcription and summary
            st.subheader("Trascrizione completa")
            st.write(full_transcript)
            if summary:
                st.subheader("Riassunto")
                st.write(summary)

            # Email sending section
            st.subheader("Invia trascrizione via email")
            email = st.text_input("Inserisci il tuo indirizzo email")
            send_email_button = st.button("Invia Email")
            
            if send_email_button:
                if not email:
                    st.error("Per favore, inserisci un indirizzo email valido.")
                else:
                    email_body = f"<h2>Trascrizione</h2><p>{full_transcript}</p>"
                    if summary:
                        email_body += f"<h2>Riassunto</h2><p>{summary}</p>"
                    status_code, response = send_email(api_keys["resend_api_key"], email, "Trascrizione Audio", email_body)
                    if status_code == 200:
                        st.success("Email inviata con successo!")
                    else:
                        st.error(f"Errore nell'invio dell'email: {response}")

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit, OpenAI, AssemblyAI e Resend")
