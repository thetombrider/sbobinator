import streamlit as st
from openai import OpenAI
import tempfile
import os

st.set_page_config(layout="wide")

# Sidebar for API key input
st.sidebar.title("Configurazioni")
api_key = st.sidebar.text_input("Inserisci la tua API Key", type="password")

st.title("Trascrittore Audio")

# Main content
uploaded_file = st.file_uploader("Trascina e rilascia qui il tuo file audio o clicca per selezionarlo", type=["wav", "mp3", "m4a", "ogg", "flac"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")

    if st.button("Trascrivi"):
        if not api_key:
            st.error("Inserisci la tua API Key nella barra laterale.")
        else:
            try:
                client = OpenAI(api_key=api_key)

                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                with st.spinner("Sto trascrivendo..."):
                    with open(tmp_file_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )

                st.subheader("Trascrizione:")
                st.write(transcript.text)

                os.unlink(tmp_file_path)
            except Exception as e:
                st.error(f"Errore: {str(e)}")