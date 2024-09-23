import streamlit as st
from openai import OpenAI
import os
import textwrap

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
        max_tokens=400
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
                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")