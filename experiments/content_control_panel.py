import streamlit as st
import requests  # For HTTP requests to the content pipeline (replace with actual endpoint)
# from pymongo import MongoClient  # Uncomment if using MongoDB or adjust for your database

st.title("Content Vormgeven")

# Geselecteerd college
st.header("Geselecteerd College")
st.image("example_thumbnail.png", width=250)

# Soorten vragen (Question Types)
st.header("Soorten Vragen")
st.write("Selecteer de soorten vragen die je wilt opnemen in het leertraject.")

question_types = {
    "mc_questions": {
        "label": "Multiple Choice (MC) Vragen",
        "example": "Wat is de hoofdfunctie van het hormoon XNP2?\nA) Regulatie van slaap\nB) Regulatie van stofwisseling\nC) Regulatie van groei\nD) Regulatie van bloeddruk",
    },
    "open_questions": {
        "label": "Open Vragen",
        "example": "Beschrijf de interactie tussen het hormoon XNP2 en H3b.",
    },
    "case_questions": {
        "label": "Case Vragen",
        "example": "Analyseer de volgende casus waarin een patiënt symptomen vertoont van een verstoorde XNP2-H3b interactie.",
    },
    "essay_questions": {
        "label": "Essay Vragen",
        "example": "Evalueer de impact van hormonale interacties op het menselijk metabolisme.",
    },
}

selected_question_types = {}
for key, value in question_types.items():
    checkbox = st.checkbox(value["label"], key=key)
    selected_question_types[key] = checkbox
    if checkbox:
        with st.expander(f"Voorbeeld van {value['label']}"):
            st.write(value["example"])

if not any(selected_question_types.values()):
    st.warning("Selecteer ten minste één soort vraag.")

# Diepgang (Level of Detail)
st.header("Diepgang")
st.write("Kies de gewenste mate van detail voor het leertraject.")

detail_options = [
    "Zeer gedetailleerd",
    "Gedetailleerd",
    "Gemiddeld",
    "Globaal",
    "Zeer globaal",
]
level_of_detail = st.select_slider(
    "Hoeveel detail moet het leertraject bevatten?",
    options=detail_options,
    value="Gemiddeld",
)
detail_examples = {
    "Zeer gedetailleerd": "Het hormoon XNP2 heeft om het uur een drie minuut durende interactie met H3b.",
    "Gedetailleerd": "Het hormoon XNP2 interageert regelmatig met H3b.",
    "Gemiddeld": "XNP2 en H3b interageren soms.",
    "Globaal": "Twee hormonen interageren met elkaar.",
    "Zeer globaal": "Hormonen kunnen interageren.",
}

st.write("Voorbeeld:")
st.write(detail_examples[level_of_detail])

# Hoofd- en bijzaken (Main and Side Issues)
st.header("Hoofd- en Bijzaken")
st.write("Selecteer aanvullende elementen om op te nemen in het leertraject.")

examples = st.checkbox(
    "Voorbeelden, toepassingen of onderzoeksresultaten die de concepten illustreren of onderbouwen",
    key="examples",
)
personal_stories = st.checkbox("Persoonlijke verhalen", key="personal_stories")

# Collect settings
settings = {
    "question_types": selected_question_types,
    "level_of_detail": level_of_detail,
    "include_examples": examples,
    "include_personal_stories": personal_stories,
}

st.session_state["settings"] = settings


def save_settings():
    settings = st.session_state["settings"]
    # Replace with actual database connection and operation
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database"]
    db.study.course.update_one(
        {"course_id": course_id}, {"$set": settings}, upsert=True
    )
    print(f"Instellingen opgeslagen in de database: \n\n{settings}")


def activate_content_pipeline():
    settings = st.session_state["settings"]
    # Replace with the actual endpoint URL of your content pipeline
    content_pipeline_url = "http://your_content_pipeline_endpoint/generate"
    try:
        response = requests.post(content_pipeline_url, json=settings)
        if response.status_code == 200:
            st.success("De content pipeline is succesvol geactiveerd.")
        else:
            st.error(
                "Er is een fout opgetreden bij het activeren van de content pipeline."
            )
    except Exception as e:
        st.error(f"Er is een uitzondering opgetreden: {e}")
    print("Content pipeline geactiveerd met de volgende instellingen:")
    print(settings)


def send_to_content_pipeline():
    save_settings()
    activate_content_pipeline()


st.button(
    "Genereer Module", use_container_width=True, on_click=send_to_content_pipeline
)
