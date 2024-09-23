import streamlit as st
from openai import OpenAI
import os
import textwrap
from functions import send_email  # Import the send_email function

st.set_page_config(
    page_title="Summarizer",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
)

# Load API keys
from pages.config import load_api_keys, is_valid_openai_api_key, is_valid_assemblyai_api_key

api_keys = load_api_keys()
openai_key_valid = is_valid_openai_api_key(api_keys["openai"])
assemblyai_key_valid = is_valid_assemblyai_api_key(api_keys["assemblyai"])

client = None
if openai_key_valid:
    client = OpenAI(api_key=api_keys["openai"])

st.title("Summarizer")

if not openai_key_valid:
    st.warning("Le API keys non sono valide o mancanti. Per favore, inseriscile nella pagina di configurazione.")

uploaded_file = st.file_uploader("Carica un file di testo", type=["txt"])

def chunk_text(text, chunk_size=6000):
    return textwrap.wrap(text, chunk_size, break_long_words=False)

def summarize_chunk(client, chunk):
    prompt = f"Riassumi il seguente testo:\n\n{chunk}\n\nRiassunto:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled assistant specializing in summarizing text. Your summaries are clear, concise, and capture the essence of the content."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.text_area("Contenuto del file", file_content, height=300)

    if st.button("Genera Riassunto"):
        if not openai_key_valid:
            st.error("API Key di OpenAI non valida o mancante. Per favore, inseriscila nella pagina di configurazione.")
        else:
            with st.spinner("Sto generando il riassunto..."):
                try:
                    chunks = chunk_text(file_content)
                    chunk_summaries = []
                    
                    for chunk in chunks:
                        chunk_summary = summarize_chunk(client, chunk)
                        chunk_summaries.append(chunk_summary)
                    
                    # Combine chunk summaries
                    combined_summary = " ".join(chunk_summaries)
                    
                    # Generate final summary
                    final_summary = summarize_chunk(client, combined_summary)
                    
                    st.subheader("Riassunto:")
                    st.write(final_summary)

                    # Store the summary in session state
                    st.session_state['summary'] = final_summary

                    # Add download button for summary
                    summary_filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_riassunto.txt"
                    st.download_button(
                        label="Scarica riassunto come TXT",
                        data=final_summary,
                        file_name=summary_filename,
                        mime="text/plain"
                    )

                    # Email sending section
                    st.subheader("Invia riassunto via email")
                    email = st.text_input("Inserisci il tuo indirizzo email")

                    if st.button("Invia Email"):
                        if not email:
                            st.error("Per favore, inserisci un indirizzo email valido.")
                        else:
                            email_body = f"<h2>Riassunto</h2><p>{st.session_state['summary']}</p>"

                            with st.spinner("Invio email in corso..."):
                                status_code, response = send_email(
                                    email,
                                    "Riassunto del Testo",
                                    email_body
                                )
                                if status_code == 200:
                                    st.success("Email inviata con successo!")
                                else:
                                    st.error(f"Errore nell'invio dell'email. Codice di stato: {status_code}, Dettagli: {response}")

                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Creato da Tommy usando Streamlit, OpenAI e Resend")