import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Functie om verbinding te maken met Azure OpenAI
def connect_to_openai():
    return AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
    api_version="2024-03-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

# Functie om de OpenAI API aan te roepen en tekst te streamen
def generate_response(prompt):
    with open("./direct_feedback_prompt.txt", "r", encoding="utf-8") as f:
        role_prompt = f.read()

    stream = openai_client.chat.completions.create(
        model="learnloop",
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        stream=True
    )

    response_text = ""
    for chunk in stream:
        st.write(chunk.choices[0]['delta']['content'])
        if "choices" in chunk:
            choice = chunk["choices"][0]
            if "delta" in choice:
                st.write(choice["delta"].get("content", ""))
                print(chunk)

    st.write(response_text)

openai_client = connect_to_openai()

st.title("Real-time Azure OpenAI Text Stream")
prompt = st.text_input("Enter your prompt here:")

if st.button("Generate Response"):
    generate_response(prompt)