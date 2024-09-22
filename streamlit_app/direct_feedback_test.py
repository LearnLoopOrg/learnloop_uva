import streamlit as st
import os
from openai import AzureOpenAI
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

using_azure = False

# Functie om verbinding te maken met Azure OpenAI
def connect_to_openai():
    if using_azure == True:
        st.session_state["openai_model"] = "learnloop"
        return AzureOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),  
        api_version="2024-03-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    else:
        st.session_state["openai_model"] = "gpt-4o"
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY_2"))




# Functie om de OpenAI API aan te roepen en tekst te streamen
def generate_response(prompt):
    with open("./direct_feedback_prompt.txt", "r", encoding="utf-8") as f:
        role_prompt = f.read()


    stream = openai_client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        stream=True
    )

    st.write_stream(stream)



openai_client = connect_to_openai()

st.title("Real-time Azure OpenAI Text Stream")
prompt = st.text_input("Enter your prompt here:")

if st.button("Generate Response"):
    generate_response(prompt)

