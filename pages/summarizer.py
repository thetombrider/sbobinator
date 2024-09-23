import streamlit as st
from openai import OpenAI
import os

st.set_page_config(
    page_title="Summarizer",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
)

# Load API keys
from pages.config import load_api_keys, is_valid_openai_api_key

api_keys = load_api_keys()
if not is_valid_openai_api_key(api_keys["openai"]):
    st.error("Inserisci una API Key valida di OpenAI nella pagina di configurazione.")
    st.stop()

client = OpenAI(api_key=api_keys["openai"])

st.title("Summarizer")

uploaded_file = st.file_uploader("Carica un file di testo", type=["txt"])

if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.text_area("Contenuto del file", file_content, height=300)

if uploaded_file is not None:
    if st.button("Genera Riassunto"):
        with st.spinner("Sto generando il riassunto..."):
            try:
                prompt = f"Riassumi il seguente testo:\n\n{file_content}\n\nRiassunto:"
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a skilled assistant specializing in summarizing text. Your summaries are clear, concise, and capture the essence of the content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300
                )
                summary = response.choices[0].message.content.strip()
                st.subheader("Riassunto:")
                st.write(summary)
            except Exception as e:
                st.error(f"Si è verificato un errore: {str(e)}")