import streamlit as st
import json
import os
from openai import OpenAI
import requests
from functions import add_sidebar_content

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

def is_valid_resend_api_key(api_key):
    # Currently, Resend does not provide an endpoint to validate API keys
    # So we'll assume the user entered a valid key if it's non-empty
    return bool(api_key)

def load_api_keys():
    if "api_keys" in st.session_state:
        return st.session_state.api_keys
    else:
        return {"openai": "", "assemblyai": "", "resend_api_key": ""}

def load_and_validate_api_keys():
    keys = load_api_keys()
    if not is_valid_openai_api_key(keys["openai"]):
        keys["openai"] = ""
    if not is_valid_assemblyai_api_key(keys["assemblyai"]):
        keys["assemblyai"] = ""
    return keys

def save_api_keys(api_keys):
    st.session_state.api_keys = api_keys
    st.success("API Keys salvate correttamente nello stato della sessione!")

def app():
    st.title("Configurazione")

    # Add sidebar content
    add_sidebar_content()

    api_keys = load_api_keys()

    openai_api_key = st.text_input("API Key di OpenAI", value=api_keys.get("openai", ""), type="password")
    if openai_api_key:
        if is_valid_openai_api_key(openai_api_key):
            st.success("API Key di OpenAI valida!")
        else:
            st.error("API Key di OpenAI non valida. Ricontrolla e riprova.")

    assemblyai_api_key = st.text_input("API Key di AssemblyAI", value=api_keys.get("assemblyai", ""), type="password")
    if assemblyai_api_key:
        if is_valid_assemblyai_api_key(assemblyai_api_key):
            st.success("API Key di AssemblyAI valida!")
        else:
            st.error("API Key di AssemblyAI non valida. Ricontrolla e riprova.")

    resend_api_key = st.text_input("API Key di Resend", value=api_keys.get("resend_api_key", ""), type="password")
    if resend_api_key:
        if is_valid_resend_api_key(resend_api_key):
            st.success("API Key di Resend inserita.")
        else:
            st.error("API Key di Resend non valida. Ricontrolla e riprova.")

    if st.button("Salva API Keys"):
        new_api_keys = {
            "openai": openai_api_key,
            "assemblyai": assemblyai_api_key,
            "resend_api_key": resend_api_key
        }
        # Assuming validation passed for OpenAI and AssemblyAI
        save_api_keys(new_api_keys)
        st.success("API Keys salvate con successo!")

if __name__ == "__main__":
    app()