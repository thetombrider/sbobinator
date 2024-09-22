import streamlit as st
from openai import OpenAI
import assemblyai as aai
import tempfile
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
    summarize_transcript
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

        Creato con ❤️ da Tommy

        Versione: 1.0.0
        """
    }
)

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
                st.write(f"File size: {len(audio_data)} bytes")
                st.write(f"MIME type: {mime_type}")
        except Exception as e:
            st.error(f"Si è verificato un errore durante il download o l'elaborazione dell'audio: {str(e)}")
            st.error("Per favore, controlla l'URL e riprova. Se il problema persiste, potrebbe essere un problema temporaneo con il servizio di hosting del file.")

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
        if not audio_source or not audio_source.get("data"):
            st.error("Nessun audio caricato o scaricato. Carica un file audio o inserisci un URL valido.")
        elif transcription_option == "Senza diarizzazione (OpenAI)":
            if not api_keys["openai"] or not is_valid_openai_api_key(api_keys["openai"]):
                st.error("Inserisci una API Key valida di OpenAI nella pagina di configurazione.")
            else:
                try:
                    client = OpenAI(api_key=api_keys["openai"])

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

                    # Summarize the transcript
                    with st.spinner("Sto generando il riassunto..."):
                        summary = summarize_transcript(api_keys["openai"], transcript.text, selected_language)
                    
                    st.subheader("Riassunto:")
                    st.write(summary)

                    st.download_button(
                        label="Scarica riassunto",
                        data=summary,
                        file_name="riassunto.txt",
                        mime="text/plain"
                    )

                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")
        else:  # With diarization (AssemblyAI)
            if not api_keys["assemblyai"] or not is_valid_assemblyai_api_key(api_keys["assemblyai"]):
                st.error("Inserisci una API Key valida di AssemblyAI nella pagina di configurazione.")
            else:
                try:
                    aai.settings.api_key = api_keys["assemblyai"]
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

                    if not transcript or not transcript.utterances:
                        raise ValueError("La trascrizione non contiene utterances")

                    st.subheader("Trascrizione con diarizzazione:")
                    full_transcript = ""
                    for utterance in transcript.utterances:
                        st.write(f"Speaker {utterance.speaker}: {utterance.text}")
                        full_transcript += f"Speaker {utterance.speaker}: {utterance.text}\n"

                    st.download_button(
                        label="Scarica trascrizione",
                        data=full_transcript,
                        file_name="trascrizione_con_diarizzazione.txt",
                        mime="text/plain"
                    )

                    # Summarize the transcript
                    with st.spinner("Sto generando il riassunto..."):
                        summary = summarize_transcript(api_keys["openai"], full_transcript, selected_language)
                    
                    st.subheader("Riassunto:")
                    st.write(summary)

                    st.download_button(
                        label="Scarica riassunto",
                        data=summary,
                        file_name="riassunto.txt",
                        mime="text/plain"
                    )

                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.error(f"Si è verificato un errore durante la trascrizione: {str(e)}")
                    st.error("Stacktrace:", exc_info=True)

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit, OpenAI e AssemblyAI")

