import streamlit as st
import openai
import PyPDF2
import faiss
import tiktoken
import numpy as np
import os
from dotenv import load_dotenv

# Laad omgevingsvariabelen
load_dotenv()
openai.api_key = os.getenv("PERSONAL_OPENAI_API_KEY")

# Controleer of de API-sleutel is ingesteld
if not openai.api_key:
    openai.api_key = st.sidebar.text_input(
        "Voer uw OpenAI API-sleutel in:", type="password"
    )


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def split_text_into_chunks(text, max_tokens=500):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


def get_embedding(text):
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    embedding = response["data"][0]["embedding"]
    return embedding


def build_vector_index(chunks):
    embeddings = []
    for chunk in chunks:
        embedding = get_embedding(chunk)
        embeddings.append(embedding)
    embeddings = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index


def generate_answer(question, index, chunks, k=3):
    # Verkrijg embedding voor de vraag
    question_embedding = get_embedding(question)
    question_embedding = np.array(question_embedding).astype("float32").reshape(1, -1)

    # Zoek naar vergelijkbare chunks
    distances, indices = index.search(question_embedding, k)
    relevant_chunks = [chunks[i] for i in indices[0]]

    # Bouw de berichten voor het chatmodel
    context = "\n\n".join(relevant_chunks)
    messages = [
        {
            "role": "system",
            "content": "Je bent een behulpzame assistent die vragen beantwoordt op basis van de gegeven context.",
        },
        {"role": "user", "content": f"Context: {context}\n\nVraag: {question}"},
    ]

    # Genereer het antwoord
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.0,
    )
    answer = response["choices"][0]["message"]["content"].strip()
    return answer


def main():
    st.title("RAG Chatbot met Document Upload")

    # Bestandsuploader
    uploaded_files = st.file_uploader(
        "Upload uw documenten", type=["pdf", "txt"], accept_multiple_files=True
    )

    if uploaded_files:
        # Verwerk de geüploade bestanden
        all_text = ""
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "text/plain":
                text = str(uploaded_file.read(), "utf-8")
            else:
                st.warning("Ongesteund bestandstype.")
                continue
            all_text += text + "\n"

        # Split tekst in chunks
        text_chunks = split_text_into_chunks(all_text)

        # Genereer embeddings en bouw de vectorindex
        with st.spinner("Bezig met het bouwen van de index..."):
            vector_index = build_vector_index(text_chunks)

        # Chatbot interactie
        if "conversation" not in st.session_state:
            st.session_state.conversation = []

        user_input = st.text_input("Stel een vraag over uw documenten:")

        if user_input:
            with st.spinner("Bezig met het genereren van een antwoord..."):
                response = generate_answer(user_input, vector_index, text_chunks)
            st.session_state.conversation.append((user_input, response))

        if st.session_state.conversation:
            for user_q, bot_a in st.session_state.conversation:
                st.write(f"**U:** {user_q}")
                st.write(f"**Chatbot:** {bot_a}")
    else:
        st.info("Upload alstublieft documenten om te beginnen.")


def llm_response(query):
    """
    Deze functie roept het OpenAI model aan en retourneert een antwoord op de query.
    """
    try:
        response = openai.Completion.create(
            engine="o1-preview",
            prompt=query,
            max_tokens=100,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Er is een fout opgetreden: {e}"


def chat():
    # Vraag van de gebruiker invoeren
    user_input = st.text_input("Stel je vraag aan het taalmodel:")

    # Wanneer er input is van de gebruiker
    if user_input:
        # Krijg het antwoord van de LLM via de functie
        answer = llm_response(user_input)

        # Toon het antwoord
        st.write("Antwoord van het model:")
        st.write(answer)


if __name__ == "__main__":
    chat()
    main()
