import streamlit as st
import json
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def evaluate_answer(max_retries=3):
    """Evaluates the answer of the student and returns a score and feedback."""
    # Creëer de user prompt met de vraag, correct antwoord en student antwoord
    prompt = f"""Input:\n
    Vraag: {st.session_state.segment_content['question']}\n
    Antwoord student: {st.session_state.student_answer}\n
    Beoordelingsrubriek: {st.session_state.segment_content['answer']}\n
    Output:\n"""

    # Lees de role prompt uit een bestand
    with open(
        "../student_app/src/assets/prompts/direct_feedback_prompt.txt",
        "r",
        encoding="utf-8",
    ) as f:
        role_prompt = f.read()
    attempt = 0
    while attempt < max_retries:
        try:
            response = st.session_state.openai_client.chat.completions.create(
                model=st.session_state.openai_model,
                messages=[
                    {"role": "system", "content": role_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            # Probeer de JSON response te laden
            feedback = json.loads(response.choices[0].message.content)

            # Definieer de vereiste top-level velden
            required_top_fields = [
                "deelantwoorden",
                "score",
                "juiste_feedback",
                "gedeeltelijk_juiste_feedback",
                "onjuiste_feedback",
                "ontbrekende_elementen",
            ]

            # Controleer of alle vereiste top-level velden aanwezig zijn
            if not all(field in feedback for field in required_top_fields):
                raise ValueError("Niet alle vereiste top-level velden zijn aanwezig.")

            # Controleer of 'deelantwoorden' een lijst is
            if not isinstance(feedback["deelantwoorden"], list):
                raise TypeError("'deelantwoorden' moet een lijst zijn.")

            # Definieer de vereiste velden voor elk deelantwoord
            required_sub_fields = ["tekst", "beoordeling", "feedback"]

            # Controleer elk deelantwoord
            for idx, deelantwoord in enumerate(feedback["deelantwoorden"], start=1):
                if not isinstance(deelantwoord, dict):
                    raise TypeError(f"Deelantwoord {idx} moet een object zijn.")
                if not all(
                    sub_field in deelantwoord for sub_field in required_sub_fields
                ):
                    raise ValueError(
                        f"Deelantwoord {idx} mist een van de vereiste velden: {required_sub_fields}"
                    )
                # Optioneel: Controleer of de waarden van de subvelden strings zijn
                for sub_field in required_sub_fields:
                    if not isinstance(deelantwoord[sub_field], str):
                        raise TypeError(
                            f"De waarde van '{sub_field}' in deelantwoord {idx} moet een string zijn."
                        )

            # Controleer het formaat van 'score' (bijvoorbeeld "2/3")
            if (
                not isinstance(feedback["score"], str)
                or not feedback["score"].count("/") == 1
            ):
                raise ValueError(
                    "'score' moet een string zijn in het formaat 'behaalde punten/max punten', bijvoorbeeld '2/3'."
                )
            punten_behaald, punten_max = feedback["score"].split("/")

            # Optioneel: Controleer dat de overige feedbackvelden strings zijn
            additional_feedback_fields = [
                "juiste_feedback",
                "gedeeltelijk_juiste_feedback",
                "onjuiste_feedback",
                "ontbrekende_elementen",
            ]
            for field in additional_feedback_fields:
                if not isinstance(feedback[field], str):
                    raise TypeError(f"'{field}' moet een string zijn.")

            # Als alle controles slagen, sla de feedback op en beëindig de retry-lus
            st.session_state.feedback = feedback
            st.session_state.score = feedback["score"]
            break  # Succes, verlaat de while-lus

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # Fout bij het parsen van JSON of bij validatie van de velden
            attempt += 1
            print(f"Feedback: {feedback}")
            print(
                f"Attempt {attempt}: Fout bij verwerken van feedback: {e}. Proberen opnieuw..."
            )

    else:
        # Als na max_retries pogingen nog steeds niet alle velden correct zijn
        st.session_state.feedback = {
            "deelantwoorden": [],
            "score": "0/3",
            "juiste_feedback": "",
            "gedeeltelijk_juiste_feedback": "",
            "onjuiste_feedback": "",
            "ontbrekende_elementen": "Er is een fout opgetreden bij het genereren van de feedback. Probeer het later opnieuw.",
        }
        st.session_state.score = st.session_state.feedback["score"]


def render_feedback():
    kleur_ontbrekend = "#c0c0c0"
    kleur_groen_licht = "#d5fdcd"
    kleur_oranje_licht = "#ffebbf"
    kleur_rood_licht = "#ffd4d8"
    kleur_groen = "#99eb89"
    kleur_oranje = "#ffd16b"
    kleur_rood = "#ff8691"
    # Gecombineerde color mapping
    color_mapping = {
        "Juist": kleur_groen_licht,
        "Gedeeltelijk juist": kleur_oranje_licht,
        "Onjuist": kleur_rood_licht,
        "juiste_feedback": kleur_groen_licht,
        "gedeeltelijk_juiste_feedback": kleur_oranje_licht,
        "onjuiste_feedback": kleur_rood,
        "ontbrekende_elementen": kleur_ontbrekend,
    }

    feedback_data = st.session_state.get("feedback", {})
    deelantwoorden = feedback_data.get("deelantwoorden", [])
    st.write(feedback_data)
    # html_content = """<span><strong>Jouw antwoord: </strong></span><br>"""
    html_content = ""
    for deel in deelantwoorden:
        beoordeling = deel.get("beoordeling", "")
        tekst = deel.get("tekst", "")
        kleur = color_mapping.get(
            beoordeling, "#ffffff"
        )  # Default naar wit als niet gevonden

        # HTML creëren voor de inline tekst met tooltip
        html_content += f"""<span style="background-color: {kleur}; border-radius: 3px; padding: 2px 5px 2px 5px; font-size: 18px;">{tekst.strip()}</span> """
    st.markdown(html_content, unsafe_allow_html=True)

    feedback_header = """<hr style="margin: 3px 0px 3px 0px; border-top: 1px solid #ccc;" />
    <h5 style="margin-top: 3px;">Feedback: </h5>"""
    st.markdown(feedback_header, unsafe_allow_html=True)

    # Toon de gecombineerde HTML-content
    ontbrekende_elementen_html = ""
    ontbrekende_elementen = feedback_data.get("ontbrekende_elementen", "")
    if ontbrekende_elementen != "":
        if "Benoem in je antwoord ook" in ontbrekende_elementen:
            ontbrekende_elementen = ontbrekende_elementen.replace(
                "Benoem in je antwoord ook",
                "<strong>Benoem in je antwoord ook</strong>",
            )
        ontbrekende_elementen_html += f"""
            <div style="border-left: 7px solid {kleur_ontbrekend}; border-radius: 5px; padding: 5px 10px; margin-bottom: 10px;">
                🗣️  {ontbrekende_elementen}
            </div>
            """
        st.markdown(
            ontbrekende_elementen_html,
            unsafe_allow_html=True,
        )
    # Functie om feedbacksecties te renderen
    feedback_keys = {
        "juiste_feedback": "✅",
        "gedeeltelijk_juiste_feedback": "🔶",
        "onjuiste_feedback": "❌",
    }
    feedback_html = ""
    for feedback_key, emoji in feedback_keys.items():
        feedback_content = feedback_data.get(feedback_key, "")
        if feedback_content != "":
            kleur = color_mapping.get(feedback_key, "#ffffff")
            # ALLEEN DE LINKERKANT HEEFT EEN KLEUR
            feedback_html += f"""
                <div style="border-left: 7px solid {kleur}; border-radius: 5px; padding: 5px 10px; margin-bottom: 10px;">
                    {emoji}  {feedback_content}
                </div>
            """
            # DE LINKERKANT EN DE BOVENKANT HEBBEN EEN KLEUR
            # feedback_html = f"""
            #     <div style="border-left: 7px solid {kleur}; border-right: 7px solid {kleur}; border-radius: 5px; padding: 5px 10px; margin-bottom: 10px;">
            #         {feedback_content}
            #     </div>
            # """
    st.markdown(feedback_html, unsafe_allow_html=True)
    # Toon score
    score = st.session_state.get("score", "0/0")
    try:
        behaalde_punten, max_punten = score.split("/")
    except ValueError:
        behaalde_punten, max_punten = "0", "0"

    punten_html = f"""
        <div style="background-color: #f0f0f0; border-radius: 5px; padding: 10px; margin-bottom: 10px">
            <strong>Punten:</strong> {behaalde_punten} / {max_punten}
        </div>
    """
    st.markdown(punten_html, unsafe_allow_html=True)


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
            evaluate_answer()

        render_feedback()
    else:
        render_answerbox()
        if st.session_state.student_answer:
            set_submitted_true()
            st.rerun()
        render_check_button()
