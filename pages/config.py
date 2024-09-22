import streamlit as st
import json
import os
from openai import OpenAI
import requests

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

def load_api_keys():
    if 'api_keys' not in st.session_state:
        try:
            st.session_state.api_keys = st.secrets["api_keys"]
        except KeyError:
            st.session_state.api_keys = {"openai": "", "assemblyai": ""}
    return st.session_state.api_keys

def load_and_validate_api_keys():
    keys = load_api_keys()
    if not is_valid_openai_api_key(keys["openai"]):
        keys["openai"] = ""
    if not is_valid_assemblyai_api_key(keys["assemblyai"]):
        keys["assemblyai"] = ""
    return keys

def save_api_keys(api_keys):
    st.session_state.api_keys = api_keys
    st.success("API Keys saved successfully in session state!")

def app():
    st.title("Configurazione")

    # Add this section for sidebar navigation
    st.sidebar.title("Navigation")

    api_keys = load_api_keys()

    openai_api_key = st.text_input("API Key di OpenAI", value=api_keys["openai"], type="password")
    if openai_api_key:
        if is_valid_openai_api_key(openai_api_key):
            st.success("API Key di OpenAI valida!")
        else:
            st.error("API Key di OpenAI non valida. Ricontrolla e riprova.")

    assemblyai_api_key = st.text_input("API Key di AssemblyAI", value=api_keys["assemblyai"], type="password")
    if assemblyai_api_key:
        if is_valid_assemblyai_api_key(assemblyai_api_key):
            st.success("API Key di AssemblyAI valida!")
        else:
            st.error("API Key di AssemblyAI non valida. Ricontrolla e riprova.")

    if st.button("Salva API Keys"):
        new_api_keys = {
            "openai": openai_api_key,
            "assemblyai": assemblyai_api_key
        }
        if is_valid_openai_api_key(openai_api_key) and is_valid_assemblyai_api_key(assemblyai_api_key):
            save_api_keys(new_api_keys)
        else:
            st.error("Una o entrambe le API Keys non sono valide. Correggi e riprova.")

if __name__ == "__main__":
    app()