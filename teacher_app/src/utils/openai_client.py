from datetime import timedelta
import os
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv
import json
import streamlit as st
from typing import Literal

load_dotenv()


def connect_to_openai(
    llm_model: Literal["gpt-4o", "azure_gpt-4", "azure_gpt-4_turbo"] = "gpt-4o",
):
    if llm_model == "gpt-4o":
        print("Using OpenAI GPT-4o")
        st.session_state.openai_model = "gpt-4o"
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY_2"))

    elif llm_model == "azure_gpt-4":
        print("Using Azure GPT-4")
        st.session_state.openai_model = "learnloop"
        return AzureOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version="2024-03-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

    elif llm_model == "azure_gpt-4_turbo":
        # TODO: not working
        # TODO: ask Gerrit to put key in Azure secrets for deployment

        st.session_state.openai_model = "learnloop"
        return AzureOpenAI(
            api_key=os.getenv("OPENAI_API_KEY_TURBO"),
            api_version="2024-03-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_TURBO"),
        )


@st.cache_data(ttl=timedelta(hours=4), show_spinner=False)
def openai_call(_client, system_message, user_message, json_response=False):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    response = None
    if json_response:
        response = _client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=1024,
            messages=messages,
        )
    else:
        response = _client.chat.completions.create(
            model="gpt-4o", temperature=0.2, messages=messages
        )

    content = response.choices[0].message.content
    if json_response:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Should be handled in caller
            st.error("Fout bij het decoderen van JSON respons.")
            return None
    return content


@st.cache_data(ttl=timedelta(hours=4))
def read_prompt(prompt_name):
    prompt_path = f"./src/prompts/{prompt_name}.txt"
    with open(prompt_path, "r") as f:
        prompt = f.read()
    return prompt
