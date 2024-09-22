from openai import OpenAI
import streamlit as st
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

st.write(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
st.write(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")

def connect_to_openai():
    return AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
    api_version="2024-03-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

client = connect_to_openai()

st.title("ChatGPT-like clone")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "learnloop"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"You balou: {prompt}")

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
