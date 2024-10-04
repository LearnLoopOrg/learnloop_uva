import streamlit as st
import json
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def render_student_answer():
    student_answer = """
    <h1 style='font-size: 20px; margin: 15px 0 10px 10px; padding: 0;'>Jouw antwoord:</h1>
    """
    st.markdown(student_answer, unsafe_allow_html=True)


def evaluate_answer():
    """Evaluates the answer of the student and returns a score and feedback."""
    # Create user prompt with the question, correct answer and student answer
    prompt = f"""Input:\n
    Vraag: {st.session_state.segment_content['question']}\n
    Antwoord student: {st.session_state.student_answer}\n
    Beoordelingsrubriek: {st.session_state.segment_content['answer']}\n
    Output:\n"""

    # Read the role prompt from a file
    with open("./experiments/feedback_prompt.txt", "r", encoding="utf-8") as f:
        role_prompt = f.read()

    response = st.session_state.openai_client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        response_format={"type": "json_object"},
    )
    st.session_state.feedback_response = json.loads(response.choices[0].message.content)


def render_feedback():
    color_mapping = {
        "Juist": "#63f730",  # Groen
        "Gedeeltelijk juist": "#ff9900",  # Oranje
        "Fout": "#f74444",  # Rood
    }

    # CSS styling voor de gemarkeerde delen en tooltips
    st.markdown(
        """
        <style>
        .highlight {
            position: relative;
            cursor: pointer;
            border-radius: 5px;
            padding: 2px 4px;
        }

        .highlight:hover::after {
            content: attr(data-feedback);
            position: absolute;
            background-color: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 8px;
            border-radius: 5px;
            top: 100%;
            left: 0;
            white-space: pre-wrap;
            z-index: 10;
            width: max-content;
            max-width: 300px;
            font-size: 12px;
        }

        /* Optionele overgangseffecten */
        .highlight::after {
            opacity: 0;
            transition: opacity 0.3s;
        }

        .highlight:hover::after {
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    deelantwoorden = st.session_state.feedback_response["deelantwoorden"]

    html_content = ""

    for idx, deel in enumerate(deelantwoorden, 1):
        beoordeling = deel["beoordeling"]
        tekst = deel["tekst"]
        feedback = deel["feedback"]
        kleur = color_mapping.get(
            beoordeling, "#ffffff"
        )  # Default to white if not found

        # Create HTML for the inline text with tooltip
        html_content += f"""<span style="background-color: {kleur}" class="highlight" data-feedback="{feedback}">{tekst.strip()}</span>"""

    # Display the combined HTML content
    st.markdown(html_content, unsafe_allow_html=True)
    punten = st.session_state.feedback_response["punten"]
    punten_html = f"""
            <div style="background-color: #f0f0f0; border-radius: 5px; padding: 10px; margin-top: 20px;">
                <strong>Punten:</strong> {punten["behaalde_punten"]} / {punten["max_punten"]}
            </div>
        """
    st.markdown(punten_html, unsafe_allow_html=True)

    # Display algemene feedback
    algemene_feedback = st.session_state.feedback_response["algemene_feedback"]
    feedback_html = f"""
            <div style="background-color: #e7f3f8; border-radius: 5px; padding: 10px; margin-top: 10px;">
                <strong>Algemene Feedback:</strong>
                <p>{algemene_feedback}</p>
            </div>
        """
    st.markdown(feedback_html, unsafe_allow_html=True)


# Data die het antwoord van de student vertegenwoordigt


def render_check_button():
    st.button("Controleer", use_container_width=True, on_click=set_submitted_true)


def set_submitted_true():
    """Whithout this helper function the user will have to press "check" button twice before submitting"""
    st.session_state.submitted = True


def render_answerbox():
    # if the image directory is present in the JSON for this segment, then display the image
    # Render a textbox in which the student can type their answer.
    st.text_area(
        label="Your answer",
        label_visibility="hidden",
        placeholder="Type your answer",
        key="student_answer",
    )


if __name__ == "__main__":
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "segment_content" not in st.session_state:
        st.session_state.segment_content = {
            "question": "Leg uit wat fotosynthese is, hoe het proces verloopt en waar het plaatsvindt.",
            "answer": "Fotosynthese is het proces waarbij planten, algen en sommige bacteriën zonlicht omzetten in energie. (1 punt) Tijdens fotosynthese wordt koolstofdioxide en water omgezet in glucose en zuurstof. (1 punt) Het proces vindt voornamelijk plaats in de chloroplasten van plantencellen. (1 punt)",
        }
    if "openai_client" not in st.session_state:
        AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        st.session_state.openai_client = AzureOpenAI(
            api_key=OPENAI_API_KEY,
            api_version="2024-04-01-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "learnloop-4o"

    # student_response = {
    #     "antwoord": "Fotosynthese is een proces waarbij planten zonlicht gebruiken om voedsel te maken. Het vindt plaats in de bladeren van planten.",
    #     "deelantwoorden": [
    #         {
    #             "tekst": "Fotosynthese is een proces waarbij planten zonlicht gebruiken om voedsel te maken.",
    #             "beoordeling": "Juist",
    #             "feedback": "Dit deel is correct. Je hebt duidelijk uitgelegd dat planten zonlicht gebruiken om voedsel te produceren, wat de kern van fotosynthese is.",
    #         },
    #         {
    #             "tekst": "Het vindt plaats in de bladeren van planten.",
    #             "beoordeling": "Gedeeltelijk juist",
    #             "feedback": "Het is juist dat fotosynthese in de bladeren plaatsvindt, maar specifieker vindt het proces plaats in de chloroplasten, die zich in de cellen van de bladeren bevinden.",
    #         },
    #     ],
    #     "punten": {"behaalde_punten": 1.5, "max_punten": 3},
    #     "algemene_feedback": "Je hebt een goed begin gemaakt door uit te leggen wat fotosynthese is en waar het plaatsvindt. Waar het plaatsvindt kon nog concreter in je uitleg en het proces zelf is niet volledig beschreven.",
    # }

    # Mapping beoordelingen naar kleuren

    st.subheader(
        "Leg uit wat fotosynthese is, hoe het proces verloopt en waar het plaatsvindt."
    )

    if st.session_state.submitted:
        # Spinner that displays during evaluating answer
        with st.spinner(
            "Een large language model (LLM) checkt je antwoord met het antwoordmodel. \
                        Check zelf het antwoordmodel als je twijfelt. \n\n Leer meer over het gebruik \
                        van LLM's op de pagina **'Uitleg mogelijkheden & limitaties LLM's'** onder \
                        het kopje 'Extra info' in de sidebar."
        ):
            render_student_answer()
            evaluate_answer()

        render_feedback()
    else:
        render_answerbox()
        if st.session_state.student_answer:
            set_submitted_true()
            st.rerun()
        render_check_button()
