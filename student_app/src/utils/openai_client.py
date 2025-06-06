from datetime import timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import streamlit as st
from typing import Literal

load_dotenv()


def connect_to_openai(
    OpenAI_API_key,
    OpenAI_API_endpoint,
    # llm_model: Literal[
    #     "LLgpt-4o", "azure_gpt-4", "azure_gpt-4_turbo", "learnloop-4o"
    # ] = "gpt-4o",
):
    return AzureOpenAI(
        api_key=OpenAI_API_key,
        api_version="2024-04-01-preview",
        azure_endpoint=OpenAI_API_endpoint,
    )


@st.cache_data(ttl=timedelta(hours=4), show_spinner=False)
def openai_call(
    _client,
    system_message,
    user_message,
    json_response=False,
    max_tokens=1024,
    model="LLgpt-4o",
):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    response = None
    if json_response:
        response = _client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            messages=messages,
        )
    else:
        response = _client.chat.completions.create(
            model=model, temperature=0.2, messages=messages
        )

    content = response.choices[0].message.content

    if json_response:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Should be handled in caller
            with open("error.json", "w") as f:
                f.write(content)
            st.error(f"Fout bij het decoderen van JSON respons.{content}")
            return None
    return content


@st.cache_data(ttl=timedelta(hours=4))
def read_prompt(prompt_name):
    prompt_path = f"./src/prompts/{prompt_name}.txt"
    with open(prompt_path, "r") as f:
        prompt = f.read()
    return prompt
