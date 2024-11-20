import json
import argparse
import time
import random
from typing import Callable
import streamlit as st
from dotenv import load_dotenv
import os
from openai import AzureOpenAI
from openai import OpenAI
import base64
from _pages.topic_overview import TopicOverview
from utils.utils import ImageHandler
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess
from datetime import datetime, timezone
from _pages.lecture_overview import LectureOverview
from _pages.course_overview import CoursesOverview
from _pages.theory_overview import TheoryOverview
from _pages.socratic_dialogue import SocraticDialogue
from _pages.lecture_student_answers_insights import LectureInsights
from _pages.lecture_quality_check import QualityCheck
from _pages.record_lecture import Recorder
from _pages.upload import UploadPage
from utils.utils import Utils
from utils.utils import AzureUtils
from slack_sdk import WebClient
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher

# Must be called first
try:
    st.set_page_config(
        page_title="LearnLoop",
        layout="wide",
        page_icon="src/data/content/images/ll_logo_icon.png",
    )
except FileNotFoundError:
    try:
        st.set_page_config(
            page_title="LearnLoop",
            layout="wide",
            page_icon="student_app/src/data/content/images/ll_logo_icon.png",
        )
    except FileNotFoundError:
        st.set_page_config(
            page_title="LearnLoop",
            layout="wide",
            page_icon=None,
        )


load_dotenv()

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def set_global_exception_handler(custom_handler: Callable, debug: bool = False):
    import sys

    script_runner = sys.modules["streamlit.runtime.scriptrunner.script_runner"]
    original_fn: Callable = script_runner.handle_uncaught_app_exception

    def combined_fn(e: BaseException):
        if not debug:  # run custom error handling only in production
            custom_handler(e)
        original_fn(e)

    script_runner.handle_uncaught_app_exception = combined_fn


def exception_handler(e: BaseException):
    # Custom error handling
    BOT_OAUTH_TOKEN = "xoxb-7362589208226-7719097315238-curwvsQxH1PbDjnQGQstR3JN"
    try:
        client = WebClient(token=BOT_OAUTH_TOKEN)
        client.chat_postMessage(
            channel="production-errors-student-app",
            text=f"An error occurred in the student app: {e}",
            username="Bot User",
        )
    except Exception as e:
        print(e)
        pass


# Cache for 5 minutes the topics list
@st.cache_resource(ttl=300)
def connect_to_openai() -> OpenAI:
    if st.session_state.openai_model == "learnloop-4o":
        print("Using UvA instance of OpenAI GPT-4o")

        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        OPENAI_API_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    else:
        print("Using LearnLoop Azure instance of OpenAI GPT-4o")
        if st.session_state.use_keyvault:
            OPENAI_API_KEY = AzureUtils.get_secret(
                "LL-AZURE-OPENAI-API-KEY", "lluniappkv"
            )
            OPENAI_API_ENDPOINT = AzureUtils.get_secret(
                "LL-AZURE-OPENAI-API-ENDPOINT", "lluniappkv"
            )
        else:
            OPENAI_API_KEY = os.getenv("LL_AZURE_OPENAI_API_KEY")
            OPENAI_API_ENDPOINT = os.getenv("LL_AZURE_OPENAI_API_ENDPOINT")
    return AzureOpenAI(
        api_key=OPENAI_API_KEY,
        api_version="2024-04-01-preview",
        azure_endpoint=OPENAI_API_ENDPOINT,
    )


def upload_progress():
    """
    Uploads the progress of the user in the current phase to the database.
    """
    # Store path and data in variables for clarity
    topics = st.session_state.db_dal.fetch_module_topics(
        st.session_state.selected_module
    )["topics"]
    topic = topics[st.session_state.topic_index]
    segment_indices = topic["segment_indexes"]
    segment_index_to_save_progress_for_topic = st.session_state.segment_index
    if st.session_state.segment_index not in segment_indices:
        segment_index_to_save_progress_for_topic = segment_indices[0]

    learning_path = {
        f"progress.{st.session_state.selected_module}.{st.session_state.selected_phase}.last_visited_segment_index_per_topic_index.{st.session_state.topic_index}": segment_index_to_save_progress_for_topic
    }

    practice_path = (
        f"progress.{st.session_state.selected_module}.{st.session_state.selected_phase}"
    )
    practice_data = {f"{practice_path}.segment_index": st.session_state.segment_index}

    # Also upload the ordered_segment_sequence if the practice session if active
    if st.session_state.selected_phase == "practice":
        practice_data[f"{practice_path}.ordered_segment_sequence"] = (
            st.session_state.ordered_segment_sequence
        )

    # The data dict contains the paths and data
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]}, {"$set": learning_path}
    )
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]}, {"$set": practice_data}
    )


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
        f"{st.session_state.base_path}assets/prompts/direct_feedback_prompt.txt",
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


def score_to_percentage():
    """Converts a score in the form of a string to a percentage."""
    try:
        # Calculate the score percentage
        part, total = st.session_state.score.split("/")
        if total == "0":
            score_percentage = 0
        else:
            # If there is a comma (e.g. 1,5), change it to a dot
            if "," in part:
                part = part.replace(",", ".")
            score_percentage = int(float(part) / float(total) * 100)
    except Exception as e:
        st.error(f"Error calculating score: {e}")
        return  # Early exit on error

    return score_percentage


def render_mc_feedback(question):
    if question["student_answer"] == question["correct_answer"]:  # antwoord is goed
        result_html = f"""
        <div style='background-color: rgba(0, 128, 0, 0.2); padding: 10px; margin-bottom: 15px; margin-top: 28px; border-radius: 7px; display: flex; align-items: center;'> <!-- Verhoogd naar 50px voor meer ruimte -->
            <p style='font-size: 16px; margin: 8px 0 8px 10px; padding: 0;'>✅  {question['student_answer']}</p>
        </div>
        """
    else:  # antwoord is fout
        result_html = f"""
        <div style='background-color: rgba(255, 0, 0, 0.2); padding: 10px; margin-bottom: 15px; margin-top: 28px; border-radius: 7px; display: flex; align-items: center;'> <!-- Verhoogd naar 50px voor meer ruimte -->
            <p style='font-size: 16px; margin: 8px 0 8px 10px; padding: 0;'>❌  {question['student_answer']}</p>
        </div>
        <div>
        <p> Goede antwoord: {question['correct_answer']} </p>
        </div>
        """

    st.markdown(result_html, unsafe_allow_html=True)


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
        "juiste_feedback": kleur_groen,
        "gedeeltelijk_juiste_feedback": kleur_oranje,
        "onjuiste_feedback": kleur_rood,
        "ontbrekende_elementen": kleur_ontbrekend,
    }

    feedback_data = st.session_state.get("feedback", {})
    deelantwoorden = feedback_data.get("deelantwoorden", [])

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

    feedback_header = (
        """<hr style="margin: 3px 0px 5px 0px; border-top: 0.5px solid #ccc;" />"""
    )
    # """<h5 style="margin-top: 3px;">Feedback: </h5>"""
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
        <div style="
            background-color: #F0F2F6; 
            border-radius: 6px; 
            padding: 13px; 
            margin-bottom: 10px;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 16px;
            color: #31333F;
        ">
            <strong>Punten: {behaalde_punten} / {max_punten}</strong>
        </div>
        <p style="font-size: 14px; color: #B3B3B3; margin-top: 2px; margin-bottom: 6px">
            LearnLoop kan fouten maken. Check het antwoordmodel als je twijfelt.
        </p>
    """
    st.markdown(punten_html, unsafe_allow_html=True)


def render_progress_bar():
    # Change style of progressbar
    progress_bar_style = """
    <style>
    /* Change main container */
    .stProgress > div > div > div {
        height: 20px;
        border-radius: 30px;
    }
    /* Change moving part of progress bar */
    .stProgress .st-bo {
        height: 20px;
        border-radius: 30px;
    }
    </style>
    """
    st.markdown(progress_bar_style, unsafe_allow_html=True)

    phase_length = determine_phase_length()
    # Initialise progress bar or update progress that indicates the relative segment index
    if phase_length > 0:
        progress = int(((st.session_state.segment_index + 1) / phase_length * 100))
    else:
        progress = 0

    # Update the progress bar
    st.progress(progress)
    st.session_state.progress = progress


def re_insert_question(interval):
    """Copies a question that the user wants to repeat and re-insert it
    in the list that contains the segment sequence. The interval determines
    how many other questions it takes for the question to be displayed again."""
    new_pos = st.session_state.segment_index + interval

    # Make sure the new position fits in the segment sequence list
    list_length = len(st.session_state.ordered_segment_sequence)
    if new_pos > list_length:
        new_pos = list_length

    # Read value of current index that corresponds to the json index
    json_index = st.session_state.ordered_segment_sequence[
        st.session_state.segment_index
    ]

    # Insert the segment in new position
    st.session_state.ordered_segment_sequence.insert(new_pos, json_index)

    change_segment_index(1)


def render_SR_nav_buttons():
    col_prev, col1, col2, col3, col_next = st.columns([1.8, 3, 3, 3, 1.8])
    with col_prev:
        st.button(
            "Vorige",
            use_container_width=True,
            on_click=lambda: change_segment_index(-1),
        )
    with col1:
        st.button(
            "Herhaal snel ↩️",
            use_container_width=True,
            on_click=re_insert_question,
            args=(5,),
        )
    with col2:
        st.button(
            "Herhaal later 🕒",
            use_container_width=True,
            on_click=re_insert_question,
            args=(15,),
        )
    with col3:
        st.button(
            "Got it ✅",
            use_container_width=True,
            on_click=lambda: change_segment_index(1),
        )
    with col_next:
        st.button(
            "Volgende",
            use_container_width=True,
            on_click=lambda: change_segment_index(1),
        )


def render_explanation():
    with st.expander("Antwoordmodel"):
        st.markdown(st.session_state.segment_content["answer"])


def determine_phase_length():
    if st.session_state.selected_phase == "practice":
        return len(st.session_state.ordered_segment_sequence)
    else:
        return len(st.session_state.page_content["segments"])


def change_segment_index(step_direction):
    """Change the segment index based on the direction of step (previous or next)."""
    phase_length = determine_phase_length()
    while True:
        # Update segment index based on direction
        st.session_state.segment_index += step_direction

        # Ensure segment index stays within valid range
        if st.session_state.segment_index < 0:
            st.session_state.segment_index = 0
            break
        if st.session_state.segment_index > phase_length:
            st.session_state.segment_index = phase_length - 1
            break
        # if st.session_state.segment_index == phase_length - 1:
        if st.session_state.segment_index == phase_length:
            st.session_state.segment_index = 100_000
            break

        # Load new segment content
        st.session_state.segment_content = st.session_state.page_content["segments"][
            st.session_state.segment_index
        ]

        # Skip theory segments if questions_only is enabled
        if (
            not st.session_state.questions_only
            or st.session_state.segment_content["type"] != "theory"
        ):
            break

    # Prevent evaluating answer when navigating to the next or previous segment
    st.session_state.submitted = False
    st.session_state.shuffled_answers = None
    upload_progress()


def render_navigation_buttons():
    """Render the navigation buttons that allows users to move between segments."""
    sources = False  # TODO: add sources to the json in content pipeline to turn this on

    # Create two or three columns, depending on whether sources is turned on
    if sources is True:
        prev_col, source_col, next_col = st.columns(3)
        with source_col:
            with st.popover("Bron", use_container_width=True):
                slides: list[int] = st.session_state.segment_content.get("slides", [])
                st.markdown(
                    "**Relevante slides:** "
                    + ", ".join([str(slide) for slide in slides])
                )
    else:
        prev_col, next_col = st.columns([1, 1])

    if st.session_state.segment_index != 0:
        with prev_col:
            st.button(
                "Vorige",
                on_click=change_segment_index,
                args=(-1,),
                use_container_width=True,
            )

    with next_col:
        st.button(
            "Volgende",
            on_click=change_segment_index,
            args=(1,),
            use_container_width=True,
        )

    if st.session_state.selected_phase == "learning":
        temp_state = st.session_state.questions_only
        st.session_state.questions_only = st.toggle(
            "Toon geen theorie, alleen vragen", key="theory_questions"
        )

        if temp_state != st.session_state.questions_only:
            st.rerun()


def set_submitted_true():
    """Whithout this helper function the user will have to press "check" button twice before submitting"""
    st.session_state.submitted = True


def show_toggle_if_practice_page():
    if st.session_state.selected_phase == "learning":
        temp_state = st.session_state.questions_only
        st.session_state.questions_only = st.toggle(
            "Toon geen theorie, alleen vragen", key="theory_questions"
        )

        if temp_state != st.session_state.questions_only:
            st.rerun()


def render_check_and_nav_buttons():
    """Renders the previous, check and next buttons when a question is displayed."""
    col_prev_question, col_check, col_next_question = st.columns([1, 3, 1])
    if st.session_state.segment_index != 0:
        with col_prev_question:
            st.button(
                "Vorige",
                use_container_width=True,
                on_click=change_segment_index,
                args=(-1,),
            )
    with col_check:
        st.button("Controleer", use_container_width=True, on_click=set_submitted_true)
    with col_next_question:
        st.button(
            "Volgende",
            use_container_width=True,
            on_click=change_segment_index,
            args=(1,),
        )

    show_toggle_if_practice_page()


def render_info():
    """Renders the info segment with title and text."""
    # if the image directory is present in the JSON for this segment, then display the image
    render_image_if_available()

    segment = st.session_state.segment_content
    st.subheader(segment["title"])
    st.write(segment["text"])


def render_answerbox():
    # if the image directory is present in the JSON for this segment, then display the image
    # Render a textbox in which the student can type their answer.
    st.text_area(
        label="Your answer",
        label_visibility="hidden",
        placeholder="Type your answer",
        key="student_answer",
    )


def render_question():
    """Function to render the question and textbox for the students answer."""
    if "answers" in st.session_state.segment_content:
        st.subheader(st.session_state.segment_content["question"])
    else:
        number_of_points = st.session_state.segment_content["answer"].count("(1 punt)")
        if number_of_points == 0:
            st.subheader(st.session_state.segment_content["question"])
        elif number_of_points == 1:
            st.subheader(
                st.session_state.segment_content["question"]
                + f" ({number_of_points} punt)"
            )
        else:
            st.subheader(
                st.session_state.segment_content["question"]
                + f" ({number_of_points} punten)"
            )


def fetch_ordered_segment_sequence():
    """Fetches the practice segments from the database."""
    user_doc = st.session_state.db.users.find_one(
        {"username": st.session_state.user_doc["username"]}
    )
    st.session_state.ordered_segment_sequence = user_doc["progress"][
        st.session_state.selected_module
    ]["practice"]["ordered_segment_sequence"]


def update_ordered_segment_sequence(ordered_segment_sequence):
    """Updates the practice segments in the database."""
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]},
        {
            "$set": {
                f"progress.{st.session_state.selected_module}.practice.ordered_segment_sequence": ordered_segment_sequence
            }
        },
    )


def add_to_practice_phase():
    """
    Adds the current segment to the practice phase in the database if the score is lower than 100.
    """
    if score_to_percentage() < 100:
        fetch_ordered_segment_sequence()
        # Store in variable for clarity
        ordered_segment_sequence = st.session_state.ordered_segment_sequence
        segment_index = st.session_state.segment_index

        if segment_index not in ordered_segment_sequence:
            ordered_segment_sequence.append(segment_index)

        # Update practice segments in db
        update_ordered_segment_sequence(ordered_segment_sequence)


def render_start_button():
    """Start button at the beginning of a phase that the user never started."""
    st.button(
        "Start", use_container_width=True, on_click=change_segment_index, args=(1,)
    )


def render_learning_explanation():
    """Renders explanation of learning phase if the user hasn't started with
    the current phase."""
    with mid_col:
        st.markdown(
            '<p style="font-size: 30px;"><strong>📖 Leren</strong></p>',
            unsafe_allow_html=True,
        )
        # st.write("The learning phase **guides you through the concepts of a lecture** in an interactive way with **personalized feedback**. Incorrectly answered questions are automatically added to the practice phase.")
        st.write(
            "In de leerfase word je op een interactieve manier door de concepten van een college heen geleid en krijg je **direct persoonlijke feedback** op open vragen. Vragen die je niet goed hebt, komen automatisch terug in 🔄 'Herhalen'."
        )
        render_start_button()
    exit()


def render_practice_exam_explanation():
    with mid_col:
        st.markdown(
            '<p style="font-size: 30px;"><strong>✍🏽 Samenvattende vragen</strong></p>',
            unsafe_allow_html=True,
        )
        st.write(
            "Hier kun je oefenen met samenvattende vragen over de onderwerpen uit de colleges."
        )
        render_start_button()
    exit()


def initialise_learning_page():
    """
    Sets all session states to correspond with database.
    """

    if st.session_state.segment_index == -1:  # If user never started this phase
        if st.session_state.selected_module.startswith("Samenvattende"):
            render_practice_exam_explanation()
        else:
            render_learning_explanation()
    elif st.session_state.segment_index == 100_000:  # if we are at the final screen
        render_final_page()
    else:
        # Select the segment (with contents) that corresponds to the saved index where the user left off
        st.session_state.segment_content = st.session_state.page_content["segments"][
            st.session_state.segment_index
        ]
        reset_submitted_if_page_changed()


def reset_segment_index_and_feedback():
    """
    When the user wants to go back to the beginning of the phase, the feedback progress
    is reset.
    """
    # Make sure that everything is reset
    st.session_state.submitted = False
    st.session_state.student_answer = None
    st.session_state.shuffled_answers = None
    st.session_state.segment_index = 0
    upload_progress()

    reset_feedback()


def reset_feedback():
    user_query = {"username": st.session_state.user_doc["username"]}
    set_empty_array = {
        "$set": {f"progress.{st.session_state.selected_module}.feedback.questions": []}
    }

    st.session_state.db.users.update_one(user_query, set_empty_array)


# render the page at the end of the learning phase (after the last question)
def render_final_page():
    questions = get_feedback_questions_from_db()
    if len(questions) == 0:
        with mid_col:
            st.subheader("Feedbackoverzicht")
            st.write(
                "Voor een overzicht van je gemaakte vragen moet je eerst vragen maken 🙃"
            )
            st.button(
                "Terug naar begin",
                on_click=reset_segment_index_and_feedback,
                use_container_width=True,
            )
        exit()

    else:
        total_score, possible_score = calculate_score()
        score_percentage = int(total_score / possible_score * 100)
        st.balloons()
        with mid_col:
            st.title("Feedbackoverzicht")
            st.markdown(
                f'<p style="font-size: 30px;"><strong>Eindscore: {total_score}/{possible_score} ({score_percentage} %) </strong></p>',
                unsafe_allow_html=True,
            )
            st.markdown("---")
            show_feedback_overview()
            st.button(
                "Terug naar begin en wis feedback",
                on_click=reset_segment_index_and_feedback,
                use_container_width=True,
            )

        # otherwise the progress bar and everything will get rendered
        exit()


def render_final_page_practice():
    with mid_col:
        st.subheader("Je bent klaar met herhalen")
        st.button(
            "Terug naar begin",
            on_click=reset_segment_index_and_feedback,
            use_container_width=True,
        )
    exit()


def calculate_score():
    questions = get_feedback_questions_from_db()
    total_score = 0
    possible_score = 0
    for question in questions:
        score_str = question.get("score", "0/1")  # Default to "0/1" if score is missing
        parts = score_str.split("/")
        total_score += float(parts[0])
        possible_score += int(parts[1])

        # If the total score is an integer, convert it to one
    if total_score.is_integer():
        total_score = int(total_score)

    return total_score, possible_score


# TODO move to db access class
def get_feedback_questions_from_db():
    query = {"username": st.session_state.user_doc["username"]}

    projection = {
        f"progress.{st.session_state.selected_module}.feedback.questions": 1,
        "_id": 0,
    }

    user_document = st.session_state.db.users.find_one(query, projection)

    if user_document is None:
        return []

    questions = (
        user_document.get("progress", {})
        .get(st.session_state.selected_module, {})
        .get("feedback", {})
        .get("questions", [])
    )

    return questions


def show_feedback_overview():
    questions = get_feedback_questions_from_db()
    for question in questions:
        st.subheader(
            f"{question['question']}"
        )  # TODO get question content not from DB but from DatabaseAccess
        if "feedback" in question:
            st.session_state.feedback = question.get("feedback", "")
            st.session_state.student_answer = question.get("student_answer", "")
            st.session_state.score = question.get("score", "")
            render_feedback()
        else:
            render_mc_feedback(question)
        st.markdown("---")


def render_oefententamen_final_page():
    with mid_col:
        st.markdown(
            '<p style="font-size: 30px;"><strong>Einde oefententamen 🎓 </strong></p>',
            unsafe_allow_html=True,
        )
        st.write("Klaar! Hoe ging het?")
        st.button(
            "Terug naar begin",
            on_click=reset_segment_index_and_feedback,
            use_container_width=True,
        )
    exit()


def reset_progress():
    """Resets the progress of the user in the current phase to the database."""
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]},
        {
            "$set": {
                f"progress.{st.session_state.selected_module}.{st.session_state.selected_phase}.segment_index": -1
            }
        },
    )


def set_if_warned_true():
    """Sets the warned variable in the database and session state to True."""
    st.session_state.db_dal.update_if_warned(True)
    st.session_state.warned = True


def render_warning():
    st.markdown(
        """
        <div style="color: #987c37; background-color: #fffced; padding: 20px; margin-bottom: 20px; border-radius: 10px;">
            Door zometeen op <strong>'controleer'</strong> te klikken, laat je het antwoord dat je ingevuld hebt controleren door een large language model (LLM). Weet je zeker dat je door wil gaan?
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("Ja", use_container_width=True, on_click=set_if_warned_true)
    st.button("Nee", on_click=reset_progress, use_container_width=True)

    st.button(
        "Leer meer over mogelijkheden & limitaties van LLM's",
        on_click=set_selected_phase,
        args=("LLM-info",),
        use_container_width=True,
    )


def progress_date_tracking_format():
    """
    The date format for the progress counter that counts the number of times
    a user visited a segment or answered a question, through dates as entries.
    It also adds the first entry directly.
    """
    date = datetime.now(timezone.utc).date()
    return {
        "type": st.session_state.db_dal.get_segment_type(
            st.session_state.segment_index
        ),
        "entries": [date.isoformat()],
    }


def add_date_to_progress_counter():
    """
    Counts how many times a person answered the current question and updates database.
    """
    module = st.session_state.selected_module

    print(
        "--------> username in add_date_to_progress_counter", st.session_state.user_doc
    )
    user_doc = st.session_state.db_dal.find_user_doc()

    progress_counter = st.session_state.db_dal.get_progress_counter(module, user_doc)

    segment_progress_count = progress_counter.get(str(st.session_state.segment_index))

    # Initialise or update date format
    if not segment_progress_count:
        segment_progress_count = progress_date_tracking_format()
    else:
        date = datetime.now(timezone.utc).date()
        segment_progress_count["entries"].append(date.isoformat())

    st.session_state.db_dal.update_progress_counter_for_segment(
        module, segment_progress_count
    )


def render_image_if_available():
    segment = st.session_state.segment_content

    if segment.get("image"):
        st.session_state.image_handler.render_image(segment, max_height=600)


def render_learning_page():
    """
    Renders the page that takes the student through the concepts of the lecture
    with info segments and questions. The student can navigate between segments
    and will get personalized feedback on their answers. Incorrectly answered
    questions are added to the practice phase.
    """
    initialise_learning_page()

    # Display the info or question in the middle column
    with mid_col:
        render_progress_bar()

        # Skip theory segment
        if (
            st.session_state.questions_only
            and st.session_state.segment_content["type"] == "theory"
        ):
            change_segment_index(1)
            initialise_learning_page()
        # Determine what type of segment to display and render interface accordingly
        if st.session_state.segment_content["type"] == "theory":
            render_info()
            add_date_to_progress_counter()
            render_navigation_buttons()

        # Open question
        if (
            st.session_state.segment_content["type"] == "question"
            and "answer" in st.session_state.segment_content
        ):
            if st.session_state.submitted:
                # Render image if present in the feedback
                render_image_if_available()

                render_question()

                # Spinner that displays during evaluating answer
                # with st.spinner(
                #     "Een large language model (LLM) checkt je antwoord met het antwoordmodel. \
                #                 Check zelf het antwoordmodel als je twijfelt. \n\n Leer meer over het gebruik \
                #                 van LLM's op de pagina **'Uitleg mogelijkheden & limitaties LLM's'** onder \
                #                 het kopje 'Extra info' in de sidebar."
                # ):
                with st.spinner(
                    "Een large language model (LLM) checkt je antwoord met het antwoordmodel."
                ):
                    evaluate_answer()
                    add_date_to_progress_counter()
                render_feedback()
                save_feedback_on_open_question()
                add_to_practice_phase()
                render_explanation()
                render_navigation_buttons()
            else:
                render_image_if_available()

                render_question()

                if st.session_state.warned is False or st.session_state.warned is None:
                    render_warning()
                else:
                    render_answerbox()

                # Becomes True if user presses ctrl + enter to evaluate answer (instead of pressing "check")
                if st.session_state.student_answer:
                    set_submitted_true()
                    st.rerun()

                if st.session_state.warned:
                    render_check_and_nav_buttons()

        # Multiple choice question
        if (
            st.session_state.segment_content["type"] == "question"
            and "answers" in st.session_state.segment_content
        ):
            render_question()

            correct_answer = st.session_state.segment_content["answers"][
                "correct_answer"
            ]
            wrong_answers = st.session_state.segment_content["answers"]["wrong_answers"]

            # Check if the answers have already been shuffled and stored
            if st.session_state.shuffled_answers is None:
                answers = [correct_answer] + wrong_answers
                random.shuffle(answers)
                st.session_state.shuffled_answers = answers
            else:
                answers = st.session_state.shuffled_answers

            if "choosen_answer" not in st.session_state:
                st.session_state.choosen_answer = None

            # Create a button for each answer
            for i, answer in enumerate(answers):
                st.button(
                    answer,
                    key=f"button{i}",
                    use_container_width=True,
                    on_click=set_submitted_answer,
                    args=(answer,),
                )

            if (
                st.session_state.choosen_answer == correct_answer
                and st.session_state.submitted
            ):
                st.success("✅ Correct!")
                st.session_state.score = "1/1"
                save_feedback_on_mc_question()
                add_date_to_progress_counter()
            # if the score is not correct, the questions is added to the practice phase
            elif st.session_state.submitted:
                st.error("❌ Incorrect. Try again.")
                st.session_state.score = "0/1"
                add_to_practice_phase()
                save_feedback_on_mc_question()
                add_date_to_progress_counter()

            # render the nav buttons
            render_navigation_buttons()


def set_submitted_answer(answer):
    st.session_state.submitted = True
    st.session_state.choosen_answer = answer
    return


def save_feedback_on_open_question():
    """
    Makes sure that the feedback to the question is saved to the database. First it checks if
    there does not already exists a feedback entry in the database. If it does, it overwrites this one,
    if it doesn't it makes a new one.
    """
    user_query = {"username": st.session_state.user_doc["username"]}

    # First, pull the existing question if it exists
    pull_query = {
        "$pull": {
            f"progress.{st.session_state.selected_module}.feedback.questions": {
                "segment_index": st.session_state.segment_index
            }
        }
    }

    # Execute the pull operation
    st.session_state.db.users.update_one(user_query, pull_query)

    # Prepare the new question data to be pushed
    # TODO remove question as it should come from DatabaseAccess
    new_question_data = {
        "question": st.session_state.segment_content["question"],
        "student_answer": st.session_state.student_answer,
        "feedback": st.session_state.feedback,
        "score": st.session_state.score,
        "segment_index": st.session_state.segment_index,
    }

    # Push the new question data
    push_query = {
        "$push": {
            f"progress.{st.session_state.selected_module}.feedback.questions": new_question_data
        }
    }

    # Execute the push operation
    st.session_state.db.users.update_one(user_query, push_query)


def save_feedback_on_mc_question():
    """
    Makes sure that the feedback to a MC question is saved to the database. First it checks if
    there does not already exists a feedback entry in the database. If it does, it overwrites this one,
    if it doesn't it makes a new one.
    """
    user_query = {"username": st.session_state.user_doc["username"]}

    # First, pull the existing question if it exists
    pull_query = {
        "$pull": {
            f"progress.{st.session_state.selected_module}.feedback.questions": {
                "segment_index": st.session_state.segment_index
            }
        }
    }

    # Execute the pull operation
    st.session_state.db.users.update_one(user_query, pull_query)

    # Prepare the new question data to be pushed
    # TODO remove question and correct_answer as they should come from DatabaseAccess
    new_question_data = {
        "question": st.session_state.segment_content["question"],
        "student_answer": st.session_state.choosen_answer,
        "correct_answer": st.session_state.segment_content["answers"]["correct_answer"],
        "score": st.session_state.score,
        "segment_index": st.session_state.segment_index,
    }

    # Push the new question data
    push_query = {
        "$push": {
            f"progress.{st.session_state.selected_module}.feedback.questions": new_question_data
        }
    }

    # Execute the push operation
    st.session_state.db.users.update_one(user_query, push_query)


def reset_submitted_if_page_changed():
    """Checks if the page changed and if so, resets submitted to false in
    order to prevent the question from being evaluated directly when opening
    a page that starts with a question."""
    st.session_state.current_page = (
        st.session_state.selected_module,
        st.session_state.selected_phase,
    )
    if st.session_state.old_page != st.session_state.current_page:
        st.session_state.submitted = False
        st.session_state.old_page = (
            st.session_state.selected_module,
            st.session_state.selected_phase,
        )


def render_practice_explanation():
    """Renders the explanation for the practice phase if the user hasn't started
    this phase in this module."""
    with mid_col:
        st.markdown(
            '<p style="font-size: 30px;"><strong>🔄 Herhalen</strong></p>',
            unsafe_allow_html=True,
        )
        # st.write("The practice phase is where you can practice the concepts you've learned in the learning phase. It uses **spaced repetition** to reinforce your memory and **improve retention.**")
        st.write(
            "Herhaal de moeilijkste vragen uit de leerfase met **_spaced repetition_** om je geheugen te versterken zodat je beter de stof onthoudt."
        )
        if st.session_state.ordered_segment_sequence == []:
            st.info(
                " Nog geen moeilijke vragen verzameld. Maak daarvoor eerst vragen uit de leerfase."
            )
        else:
            render_start_button()
    exit()


def initialise_practice_page():
    """Update all session states with database data and render practice explanation
    if it's the first time."""

    # Fetch the last segment index from db
    st.session_state.segment_index = st.session_state.db_dal.fetch_segment_index()

    if st.session_state.segment_index == -1:
        fetch_ordered_segment_sequence()
        render_practice_explanation()
    elif st.session_state.segment_index == 100_000:
        render_final_page()
    else:
        fetch_ordered_segment_sequence()

        json_index = st.session_state.ordered_segment_sequence[
            st.session_state.segment_index
        ]

        # Select the segment (with contents) that corresponds to the saved json index where the user left off
        st.session_state.segment_content = st.session_state.page_content["segments"][
            json_index
        ]

        reset_submitted_if_page_changed()


def render_practice_page():
    """
    Renders the page that contains the practice questions and
    answers without the info segments and with the spaced repetition buttons.
    This phase allows the student to practice the concepts they've learned
    during the learning phase and which they found difficult.
    """
    initialise_practice_page()

    # Display the info or question in the middle column
    with mid_col:
        render_progress_bar()

        # Determine what type of segment to display and render interface accordingly
        # info_question
        if st.session_state.segment_content["type"] == "theory":
            render_info()
            render_navigation_buttons()

        # Open question
        if (
            st.session_state.segment_content["type"] == "question"
            and "answer" in st.session_state.segment_content
        ):
            # Render image if present in the feedback
            render_image_if_available()

            render_question()
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
                save_feedback_on_open_question()
                render_explanation()
                render_SR_nav_buttons()
            else:
                if st.session_state.warned is False:
                    render_warning()
                else:
                    render_answerbox()
                    # Becomes True if user presses ctrl + enter to evaluate answer (instead of pressing "check")
                    if st.session_state.student_answer:
                        set_submitted_true()
                        st.rerun()
                    render_check_and_nav_buttons()

        # MC Question
        if (
            st.session_state.segment_content["type"] == "question"
            and "answers" in st.session_state.segment_content
        ):
            render_question()

            correct_answer = st.session_state.segment_content["answers"][
                "correct_answer"
            ]
            wrong_answers = st.session_state.segment_content["answers"]["wrong_answers"]

            # Check if the answers have already been shuffled and stored
            if st.session_state.shuffled_answers is None:
                answers = [correct_answer] + wrong_answers
                random.shuffle(answers)
                st.session_state.shuffled_answers = answers
            else:
                answers = st.session_state.shuffled_answers

            if "choosen_answer" not in st.session_state:
                st.session_state.choosen_answer = None

            # Create a button for each answer
            for i, answer in enumerate(answers):
                st.button(
                    answer,
                    key=f"button{i}",
                    use_container_width=True,
                    on_click=set_submitted_answer,
                    args=(answer,),
                )

            if (
                st.session_state.choosen_answer == correct_answer
                and st.session_state.submitted
            ):
                st.success("✅ Correct!")
                st.session_state.score = "1/1"
                save_feedback_on_mc_question()
            # if the score is not correct, the questions is added to the practice phase
            elif st.session_state.submitted:
                st.error("❌ Incorrect. Try again.")
                st.session_state.score = "0/1"
                save_feedback_on_mc_question()
            # render the nav buttons
            render_navigation_buttons()


def render_not_recorded_page():
    """
    Renders the page that shows the student that the lecture is not recorded.
    """
    lecture_name = st.session_state.selected_module
    st.title(f"College — {lecture_name}")

    st.subheader("Nog niet opgenomen")
    st.write("Dit college is (nog) niet opgenomen. Hopelijk binnenkort wel! ")
    course_name = st.session_state.selected_course
    st.button(
        "Terug naar collegeoverzicht",
        key=course_name,
        on_click=go_to_course,
        args=(course_name,),
        use_container_width=True,
    )


def go_to_course(course_name):
    """
    Callback function for the button that redirects to the course overview page.
    """
    st.session_state.selected_course = course_name
    st.session_state.selected_phase = "lectures"


def render_generated_page():
    """
    Renders the page that shows the student that the lecture is not recorded.
    """
    st.title(f"College — {st.session_state.selected_module}")
    st.session_state.utils.add_spacing(1)
    st.subheader("Nog niet nagekeken door docent")
    st.write(
        "De docent moet de content van het college nog nakijken voordat je er hiermee kunt oefenen."
    )
    course_name = st.session_state.selected_course
    st.button(
        "Terug naar collegeoverzicht",
        key=course_name,
        on_click=go_to_course,
        args=(course_name,),
        use_container_width=True,
    )


def render_LLM_info_page():
    """
    Renders the info page that contains the explanation of the learning and practice phases.
    """
    with open(
        f"{st.session_state.base_path}data/uitleg_llms_voor_student.txt", "r"
    ) as f:
        info_page = f.read()
    with mid_col:
        st.markdown(info_page, unsafe_allow_html=True)
    return


def render_selected_page():
    """
    Determines what type of page to display based on which module the user selected.
    """
    st.session_state.page_content = st.session_state.db_dal.fetch_module_content(
        st.session_state.selected_module
    )

    match st.session_state.selected_phase:
        case "courses":
            st.session_state.courses_page.run()
        case "lectures":
            st.session_state.lectures_page.run()
        case "topics":
            st.session_state.topics_page.run()
        case "learning":
            render_learning_page()
        case "practice":
            render_practice_page()
        case "theory-overview":
            st.session_state.theory_overview_page.run()
        case "socratic-dialogue":
            st.session_state.socratic_dialogue_page.run()
        case "record":
            st.session_state.record_page.run()
        case "upload":
            st.session_state.upload_page.run()
        case "quality-check":
            st.session_state.quality_check_page.run()
        case "insights":
            st.session_state.insights_page.run()
        case "not-recorded":
            render_not_recorded_page()
        case "generated":
            render_generated_page()
        case "LLM-info":
            render_LLM_info_page()

        case _:  # Render this page by default
            st.session_state.lectures_page.run()


def upload_feedback():
    """Uploads feedback to the database."""
    st.session_state.db.feedback.insert_one({"feedback": st.session_state.feedback_box})
    st.session_state.feedback_submitted = True


def render_feedback_form():
    """Feedback form in the sidebar."""
    with st.sidebar:
        st.text_area(
            label="Wat vind je handig? Wat kan beter? Voer geen persoonlijke of herkenbare gegevens in.",
            key="feedback_box",
        )
        st.button("Verstuur", on_click=upload_feedback, use_container_width=True)

        if st.session_state.get("feedback_submitted", False):
            st.success("Bedankt voor je feedback!")
            st.balloons()
            time.sleep(2)
            st.session_state.feedback_submitted = False
            st.experimental_rerun()


def render_info_page():
    """Renders the info page that contains the explanation of the learning and practice phases."""
    with open(
        f"{st.session_state.base_path}data/uitleg_llms_voor_student.txt", "r"
    ) as f:
        info_page = f.read()
    with mid_col:
        st.markdown(info_page, unsafe_allow_html=True)
    return


def track_visits():
    """Tracks the visits to the modules."""
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]},
        {
            "$inc": {
                f"progress.{st.session_state.selected_module}.visits.{st.session_state.selected_phase}": 1
            }
        },
    )


def set_selected_phase(phase):
    st.session_state.selected_phase = phase
    # update the selected phase in the database
    st.session_state.db_dal.update_last_phase(phase)


def logout():
    st.session_state.user_doc = None
    st.session_state.selected_module = None
    st.session_state.selected_phase = None
    st.session_state.logged_in = False
    st.session_state.db_switched = False
    return


def render_sidebar():
    """
    Function to render the sidebar with the modules and login module.
    """
    with st.sidebar:
        img_cols = st.columns([1, 3])
        with img_cols[1]:
            logo_base64 = convert_image_base64(
                f"{st.session_state.base_path}data/content/images/logo.png"
            )
            img_html = f"""
            <div style="margin-top: 0px; margin-bottom: 40px">
                <img src="data:image/png;base64,{logo_base64}" style="width: 110px;" />
            </div>
            """
            st.markdown(img_html, unsafe_allow_html=True)

        st.divider()

        st.button(
            "📚 Mijn vakken",
            on_click=set_selected_phase,
            args=("courses",),
            use_container_width=True,
        )
        if st.session_state.user_doc["role"] == "teacher":
            st.button(
                "➕ Creëer module",
                on_click=set_selected_phase,
                args=("upload",),
                use_container_width=True,
            )
        if st.session_state.selected_phase in {
            "topics",
            "learning",
            "practice",
            "insights",
            "socratic-dialogue",
            "record",
            "quality-check",
            "theory-overview",
        }:
            st.button(
                # f"📖 Modules | {st.session_state.selected_course}",
                "📖 Terug naar modules",
                on_click=set_selected_phase,
                args=("lectures",),
                use_container_width=True,
            )
        if st.session_state.selected_phase in {
            "learning",
            "practice",
            "socratic-dialogue",
        }:
            st.button(
                "🔍 Terug naar onderwerpen",
                on_click=set_selected_phase,
                args=("topics",),
                use_container_width=True,
            )

        if (
            st.session_state.db_name == "UvA_KNP"
            and st.session_state.user_doc["role"] == "student"
        ):
            render_feedback_form()

    # Space for the menu rendered in Socratic Dialogue
    if (
        "socratic_menu_placeholder" not in st.session_state
        or st.session_state.socratic_menu_placeholder is None
    ):
        st.session_state.socratic_menu_placeholder = st.sidebar.empty()

    if "bottom_buttons_placeholder" not in st.session_state:
        st.session_state["bottom_buttons_placeholder"] = st.sidebar.empty()

    # Render the static bottom buttons in the dedicated placeholder
    with st.session_state["bottom_buttons_placeholder"].container():
        st.divider()
        if st.session_state.user_doc["role"] == "student":
            st.button(
                "Uitleg LLM's",
                on_click=set_selected_phase,
                args=("LLM-info",),
                use_container_width=True,
                key="info_button_sidebar",
            )

        st.button("Log uit", on_click=logout, use_container_width=True)

        st.toggle("Studentweergave", key="student_view")


def create_default_progress_structure(module):
    """
    Returns the default structure for progress in any module, including the progress_counter.
    """
    empty_dict = create_empty_progress_dict(module)

    return {
        "learning": {
            "segment_index": -1,
            "progress_counter": empty_dict,
        },
        "practice": {"segment_index": -1, "ordered_segment_sequence": []},
        "feedback": {"questions": []},
    }


def create_empty_progress_dict(module):
    """
    Creates an empty dictionary with segment indices as keys and None as values for progress tracking.
    """
    st.session_state.page_content = st.session_state.db_dal.fetch_module_content(module)
    number_of_segments = (
        len(st.session_state.page_content["segments"])
        if st.session_state.page_content
        else 0
    )
    return {str(i): None for i in range(number_of_segments)}


def fetch_module_status(module_name):
    lecture = st.session_state.db.content.find_one({"lecture_name": module_name})

    if lecture:
        return lecture["status"]
    else:
        print(f"Module {module_name} not found in db")
        return None


# Cache for 10 minutes only, so it checks every 10 minutes if there is a new lecture available
# @st.cache_data(show_spinner=False, ttl=600)
def check_user_doc_and_add_missing_fields():
    """
    Initializes the user database with missing fields and modules.
    """
    user_doc = st.session_state.db_dal.find_user_doc()

    if not user_doc:
        st.session_state.db.users.insert_one(
            {"username": st.session_state.user_doc["username"]}
        )
        user_doc = st.session_state.db_dal.find_user_doc()
        print("Inserted new user doc in db: ", user_doc)

    # General fields initialization
    if "warned" not in user_doc:
        user_doc["warned"] = False
        print("Added 'warned' field to user_doc")

    if "progress" not in user_doc:
        user_doc["progress"] = {}
        print("Added 'progress' field to user_doc")

    # Check of alle course modules in user_doc["progress"] zitten
    course_catalog = st.session_state.db_dal.get_course_catalog(
        st.session_state.user_doc["university"],
        st.session_state.user_doc["courses"],
    )
    for course in course_catalog.courses:
        course_modules = st.session_state.db_dal.get_lectures_for_course(
            course.title, course_catalog
        )
        for module in course_modules:
            if fetch_module_status(module.title) == "corrected":
                if module.title not in user_doc.get("progress", {}):
                    user_doc["progress"][module.title] = (
                        create_default_progress_structure(module.title)
                    )
                    print(
                        f"Added progess structure for 'module' {module.title} to user_doc['progress']"
                    )

                if "practice" not in user_doc.get("progress", {}).get(module.title, {}):
                    print(f"practice zit niet in de db voor module {module.title}")

                    user_doc["progress"][module.title]["practice"] = {
                        "segment_index": -1,
                        "ordered_segment_sequence": [],
                    }

                    print(
                        f"Added 'practice' field for module {module.title} to user_doc['progress']"
                    )

                if "learning" not in user_doc.get("progress", {}).get(module.title, {}):
                    user_doc["progress"][module.title]["learning"] = {
                        "segment_index": -1
                    }
                    print(
                        f"Added 'learning' field for module {module.title} to user_doc['progress']"
                    )

                if "progress_counter" not in user_doc.get("progress", {}).get(
                    module.title, {}
                ).get("learning", {}):
                    empty_dict = create_empty_progress_dict(module.title)
                    user_doc["progress"][module.title]["learning"][
                        "progress_counter"
                    ] = empty_dict
                    print(
                        f"Added 'progress_counter' field for module {module.title} to user_doc['progress']"
                    )

    if "last_module" not in user_doc:
        # Zorg ervoor dat je een default module hebt als er geen modules in user_doc zijn
        user_doc["last_module"] = next(iter(user_doc.get("progress", {})), None)
        print("Added 'last_module' field to user_doc")

    # Update user_doc in db
    st.session_state.db.users.update_one(
        {"username": st.session_state.user_doc["username"]}, {"$set": user_doc}
    )


def convert_image_base64(image_path):
    """Converts image in working dir to base64 format so it is
    compatible with html."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def try_login(input_username, input_password, uni):
    # Reset verkeerde inlogstatus
    st.session_state.wrong_credentials = False

    # Clean inputs by stripping whitespace
    input_username = input_username.strip()
    input_password = input_password.strip()

    # Retrieve user from database
    print(f"Database name: {st.session_state.db_name}")
    user_doc = st.session_state.db.users.find_one({"username": input_username})
    print("user_doc", user_doc)

    # Check if input password is correct
    if user_doc and "password" in user_doc:
        hashed_password = user_doc.get("password", None)

        if Hasher.check_pw(input_password, hashed_password):
            st.session_state.user_doc = {
                "username": user_doc["username"],
                "role": user_doc["role"],
                "university": user_doc["university"],
                "courses": user_doc["courses"],
            }
            st.session_state.logged_in = True
            return

    # Gebruikerslijst voor validatie
    uva_users = {
        "Luc Mahieu": {"role": "student"},
        "Milan van Roessel": {"role": "student"},
        "eensupergeheimecode": {"role": "student"},
        "supergeheimecode": {"role": "student"},
        "famkesgeheimecode": {"role": "student"},
        "Erwin van Vliet": {"role": "teacher"},
    }

    vu_users = {}

    # Laad UU gebruikers
    with open(f"{st.session_state.base_path}data/uu_users.json", "r") as f:
        uu_users = json.load(f)

    # Controleer of de gebruikersnaam in de lijst staat
    if input_username in uva_users:
        st.session_state.user_doc = {
            "username": input_username,
            "role": uva_users[input_username]["role"],
        }
        st.session_state.logged_in = True
        st.session_state.db_name = (
            "LearnLoop" if input_username == "supergeheimecode" else "UvA_KNP"
        )

    elif input_username in vu_users:
        st.session_state.user_doc = {
            "username": input_username,
            "role": vu_users[input_username]["role"],
        }
        st.session_state.logged_in = True
        st.session_state.db_name = "test_users_1"

    elif input_username in uu_users:
        st.session_state.user_doc = {
            "username": input_username,
            "role": uu_users[input_username]["role"],
        }
        st.session_state.logged_in = True
        st.session_state.db_name = "test_users_2"

    else:
        # Onjuiste inloggegevens
        st.session_state.wrong_credentials = True
        st.session_state.logged_in = False


def inlog_terminal(uni):
    # Initialiseer session state variabelen
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "wrong_credentials" not in st.session_state:
        st.session_state.wrong_credentials = False

    # Begin een formulier voor de login
    with st.form(key=f"login_form_{uni}"):
        # Vraag de gebruikersnaam
        username = st.text_input(
            "Log in",
            label_visibility="collapsed",
            placeholder="Gebruikersnaam",
            key=f"streamlit_username_{uni}",
        )

        password = st.text_input(
            "Password",
            label_visibility="collapsed",
            placeholder="Wachtwoord",
            key=f"streamlit_password_{uni}",
            type="password",
        )

        if st.form_submit_button("Inloggen", use_container_width=True):
            # Roep de inlogfunctie aan met de ingevoerde gebruikersnaam
            try_login(username, password, uni)

    # Controleer de status van het inloggen
    if st.session_state.get("logged_in", False):
        st.rerun()
    elif st.session_state.get("wrong_credentials", False):
        st.warning("Onjuiste inloggegevens.")


def login_module():
    # @st.cache_data(ttl=600)
    def get_user_data():
        """Caches the login data for all users for 10 minutes in a accessible format."""
        # Connect to database
        db = st.session_state.db

        # List  all collections in db
        collections = list(db.users.find())  # make hashable for st.cache_data

        # Format collections into { key: { "username": username, "password": password } }
        items = {"usernames": {item["username"]: item for item in collections}}

        # Revert username field to name
        for username, item in items["usernames"].items():
            item["username"] = item.pop("username")
            item["password"] = item.pop("password")

        return items

    login_user_data = get_user_data()

    cookie_name = "LearnLoopLogin"
    cookie_key = "LearnLoopKey"
    cookie_expiry = 0
    preauthorized_users = []

    authenticator = stauth.Authenticate(
        login_user_data,
        cookie_name,
        cookie_key,
        cookie_expiry,
        preauthorized_users,
    )

    authenticator.login("Login", "main")

    if st.session_state["authentication_status"]:
        st.header("Account")
        st.write(f"{st.session_state.user_doc}")
        authenticator.logout("Log out", "main", key="unique_key")
    elif st.session_state["authentication_status"] is False:
        st.error("Username or password is incorrect")
    elif st.session_state["authentication_status"] is None:
        pass


def save_hashed_password_account_to_database():
    new_password = st.session_state.new_password
    hashed_password = Hasher.hash(new_password)
    st.session_state.db.users.insert_one(
        {
            "username": st.session_state.new_username,
            "password": hashed_password,
            "role": st.session_state.user_role,
            "university": st.session_state.user_university,
            "courses": st.session_state.user_courses,
        }
    )

    st.session_state.logged_in = True
    st.session_state.user_doc = {
        "username": st.session_state.new_username,
        "role": "student",
        "university": st.session_state.user_university,
    }

    st.session_state.admin_logged_in = False


def new_account_terminal():
    # Plaats de universiteit selectbox buiten het formulier
    university = st.selectbox(
        "University",
        [
            "Selecteer een universiteit",
            "Universiteit van Amsterdam",
            "Vrije Universiteit",
            "Universiteit Utrecht",
        ],
        index=0,
        key="user_university",
    )

    with st.form(key="new_account_form"):
        st.text_input("Username", key="new_username")
        st.text_input("Password", type="password", key="new_password")

        # Toon de vakken multiselect alleen als een universiteit is geselecteerd
        university_courses = {
            "Universiteit van Amsterdam": ["Celbiologie", "Klinische Neuropsychologie"],
            "Vrije Universiteit": [
                "None",
            ],
            "Universiteit Utrecht": ["Plant biology", "Cell biology"],
        }

        if university != "Selecteer een universiteit":
            courses = university_courses.get(university, [])
            st.multiselect("Vakken", courses, key="user_courses")

        st.selectbox("Role", ["student", "teacher"], key="user_role")

        st.form_submit_button(
            "Create account",
            on_click=save_hashed_password_account_to_database,
            use_container_width=True,
        )


def set_admin_logged_in_true():
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = True
    else:
        st.session_state.admin_logged_in = True


def render_login_page():
    """This is the first page the user sees when visiting the website and
    prompts the user to login via SURFconext."""

    # login_module()

    if st.session_state.deployment_type == "uva_servers":
        # columns = st.columns([0.5, 1.5, 0.5])
        columns = st.columns([1, 0.8, 1])
        with columns[1]:
            ll_logo_base64 = convert_image_base64(
                f"{st.session_state.base_path}data/content/images/logo.png"
            )

            html_ll_logo = f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{ll_logo_base64}" alt="Logo" style="max-width: 25%; height: auto; margin-bottom: 10px; margin-top: 0px">
            </div>
            """

            st.markdown(html_ll_logo, unsafe_allow_html=True)

            st.divider()

            if surf_test_env:
                href = "http://localhost:3000/surf"
            else:
                href = "https://learnloop.datanose.nl/surf"

            uva_logo_base64 = convert_image_base64(
                f"{st.session_state.base_path}data/content/images/uva-logo-eng.png"
            )

            html_content = f"""
            <div style="text-align: center; margin: 20px; width=100%;">
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{uva_logo_base64}" alt="Logo" style="max-width: 50%; height: auto; margin-bottom: 10px; margin-top: -20px">
                </div>
                <div style="height: 20px; margin-bottom: 50px">
                    <a href="{href}" target="_self" style="text-decoration: none;">
                        <button style="font-size: 20px; border: none; color: white; padding: 10px 20px; 
                        text-align: center; text-decoration: none; display: block; width: 100%; cursor: pointer; background-color: #4CAF50; border-radius: 10px;">SURF Login</button>
                    </a>
                </div>
            </div>"""

            st.markdown(html_content, unsafe_allow_html=True)

            st.divider()

            inlog_terminal("UvA")

            st.divider()

            with st.expander("Admin login", expanded=st.session_state.admin_logged_in):
                st.text_input(
                    "Admin login",
                    label_visibility="collapsed",
                    key="admin_key",
                )

                st.button(
                    "Log in",
                    on_click=set_admin_logged_in_true,
                    use_container_width=True,
                )

                if st.session_state.admin_logged_in:
                    if st.session_state.admin_key != "":
                        if st.session_state.admin_key == "pooLnraeL":
                            new_account_terminal()
                        else:
                            st.warning("Wrong credentials")
                    else:
                        st.warning("Enter admin key")

            # st.divider()

            # uu_logo_base64 = convert_image_base64(
            #     f"{st.session_state.base_path}data/content/images/uu-logo-nl.png"
            # )

            # html_uu_logo = f"""
            #     <div style="text-align: center;">
            #         <img src="data:image/png;base64,{uu_logo_base64}" alt="Logo" style="max-width: 48%; height: auto; margin-bottom: 30px; margin-top:0px">
            #     </div>
            # """
            # st.markdown(html_uu_logo, unsafe_allow_html=True)

            # st.info(
            #     "Log je voor het eerst in? Check dan eerst of je de uitnodiging van SURF hebt geaccepteerd (e-mail: *'Uitnodiging voor uva_fnwi_learnloop'*) om in te loggen. Niet gevonden? Check je spam. \n\nNog geen mail? Stuur een berichtje naar **+31 6 2019 2794**, dan zorgt Milan ervoor dat je toegang krijgt. 😊"
            # )
            # with st.expander("Admin login", expanded=False):
            #     st.text_input("Credentials", key="streamlit_username", type="password")
            #     if st.session_state.wrong_credentials:
            #         st.warning("Onjuiste credentials.")
            #     st.button("Log in", on_click=try_login, use_container_width=True)

    elif st.session_state.deployment_type == "streamlit_or_local":
        print("Rendering login page: streamlit_or_local")
        cols = st.columns([1, 0.7, 1])
        with cols[1]:
            img_cols = st.columns([1, 3, 1])
            with img_cols[0]:
                logo_path = f"{st.session_state.base_path}data/content/images/logo.png"
                st.image(logo_path, use_column_width=True)
            with img_cols[2]:
                vu_logo_base64 = (
                    f"{st.session_state.base_path}data/content/images/vu_logo.png"
                )
                st.image(vu_logo_base64, use_column_width=True)

            st.write("\n\n")
            st.write("\n\n")
            st.write("\n\n")

            st.text_input("Gebruikersnaam", key="streamlit_username")
            st.text_input("Wachtwoord", type="password", key="streamlit_password")

            if st.session_state.wrong_credentials:
                st.warning("Gebruikersnaam of wachtwoord is onjuist.")

            st.button("Login", use_container_width=True, on_click=try_login)


@st.cache_resource(show_spinner=False)
def initialise_data_access_layer():
    db_dal = DatabaseAccess()
    return db_dal


def determine_selected_module():
    st.session_state.selected_module = st.session_state.db_dal.fetch_last_module()
    if st.session_state.selected_module is None:
        st.session_state.selected_module = st.session_state.modules[0]


def fetch_nonce_from_query():
    return st.query_params.get("nonce", None)


def determine_username_from_nonce():
    """
    Fetches the username from the database using the nonce in the query parameters.
    """
    st.session_state.nonce = fetch_nonce_from_query()
    st.session_state.db_dal.fetch_info()


def remove_nonce_from_memories():
    """Removes the nonce from the query parameters and session state."""
    st.query_params.pop("nonce", None)
    st.session_state.db_dal.invalidate_nonce()
    st.session_state.nonce = None


def get_commandline_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--debug",
        help="Enable debug mode: which means that the app will not report errors to Slack",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--use_keyvault",
        help="Set to True to use Azure Key Vault for secrets",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--use_LL_openai_deployment",
        help="Set to True to use the LearnLoop OpenAI instance, otherwise use the UvA's",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--use_LL_cosmosdb",
        help="Set to True to use the LearnLoop CosmosDB instance, otherwise use the UvA's",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--surf_test_env",
        help="Set to True to use the SURF test environment for authentication",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no_login_page",
        help="Set to True to skip the login page",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--use_LL_blob_storage",
        help="Set to True to use the LearnLoop Blob Storage instance, otherwise use the UvA's",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--test_username",
        help="Set to a test username to use when testing (Luc Mahieu)",
        action="store",
        default=None,
    )

    parser.add_argument(
        "--run_page",
        help="Page you want to run when testing",
        action="store",
        default=None,
    )

    return parser.parse_args()


def is_deployed_in_streamlit_cloud():
    # Check if the app is deployed in Streamlit Cloud by checking if the /mount directory exists
    return os.path.exists("/mount")


def is_running_locally():
    return os.getenv("LOCAL_DEV", False)


def set_correct_settings_for_deployment_type():
    st.session_state.deployment_type = "uva_servers"

    streamlit_deployment = is_deployed_in_streamlit_cloud()
    print(f"Streamlit deployment: {streamlit_deployment}")
    running_locally = is_running_locally()
    print(f"Running locally: {running_locally}")

    if streamlit_deployment is True or running_locally is True:
        print("App is deployed in Streamlit or runs locally, use cloud arguments.")
        args.use_LL_blob_storage = True
        args.use_LL_cosmosdb = True
        args.use_LL_openai_deployment = True
        args.debug = False
        args.no_login_page = False
        base_path = "student_app/src/"
        deployment_type = "streamlit_or_local"
    elif st.session_state.deployment_type == "uva_servers":
        print("App draait op uva servers, gebruik uva path.")
        base_path = "src/"
        deployment_type = "uva_servers"
        args.no_login_page = False

    st.session_state.deployment_type = deployment_type

    return args, base_path


def initialise_variables():
    if "student_view" not in st.session_state:
        st.session_state.student_view = False

    if "user_doc" not in st.session_state:
        st.session_state.user_doc = None

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if "socratic_menu_placeholder" in st.session_state:
        st.session_state.socratic_menu_placeholder = None

    if "generated_username" not in st.session_state:
        st.session_state.generated_username = None

    if "via_qr_code" not in st.session_state:
        st.session_state.via_qr_code = False

    if "turned_qr_code_into_username" not in st.session_state:
        st.session_state.turned_qr_code_into_username = False

    if "db_switched" not in st.session_state:
        st.session_state.db_switched = False

    if "base_path" not in st.session_state:
        st.session_state.base_path = None

    if "use_LL_openai_deployment" not in st.session_state:
        st.session_state.use_LL_openai_deployment = None

    if "use_LL_cosmosdb" not in st.session_state:
        st.session_state.use_LL_cosmosdb = None

    if "use_keyvault" not in st.session_state:
        st.session_state.use_keyvault = False

    if "use_LL_blob_storage" not in st.session_state:
        st.session_state.use_LL_blob_storage = False

    if "db_name" not in st.session_state:
        st.session_state.db_name = None

    if "selected_course" not in st.session_state:
        st.session_state.selected_course = None

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = None

    if "practice_exam_name" not in st.session_state:
        st.session_state.practice_exam_name = "Samenvattende vragen"

    if "nonce" not in st.session_state:
        st.session_state.nonce = None

    if "user_doc" not in st.session_state:
        st.session_state.user_doc = {"username": None, "role": None}

    if "warned" not in st.session_state:
        st.session_state.warned = None

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False

    if "old_page" not in st.session_state:
        st.session_state.old_page = None

    if "current_page" not in st.session_state:
        st.session_state.current_page = None

    if "ordered_segment_sequence" not in st.session_state:
        st.session_state.ordered_segment_sequence = []

    if "page_content" not in st.session_state:
        st.session_state.page_content = None

    if "segment_index" not in st.session_state:
        st.session_state.segment_index = 0

    if "modules" not in st.session_state:
        st.session_state.modules = None

    if "selected_module" not in st.session_state:
        st.session_state.selected_module = None

    if "selected_phase" not in st.session_state:
        st.session_state.selected_phase = "courses"

    if "segment_content" not in st.session_state:
        st.session_state.segment_content = None

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if "student_answer" not in st.session_state:
        st.session_state.student_answer = ""

    if "score" not in st.session_state:
        st.session_state.score = ""

    if "feedback" not in st.session_state:
        st.session_state.feedback = ""

    if "shuffled_answers" not in st.session_state:
        st.session_state.shuffled_answers = None

    if "questions_only" not in st.session_state:
        st.session_state.questions_only = False

    if "deployment_type" not in st.session_state:
        st.session_state.deployment_type = None

    if "wrong_credentials" not in st.session_state:
        st.session_state.wrong_credentials = False

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "streamlit_username" not in st.session_state:
        st.session_state.streamlit_username = None

    if "streamlit_password" not in st.session_state:
        st.session_state.streamlit_password = None

    if "segments_in_qualitycheck" not in st.session_state:
        st.session_state.segments_in_qualitycheck = None

    if "previous_module" not in st.session_state:
        st.session_state.previous_module = None

    if "use_mongodb" not in st.session_state:
        st.session_state.use_mongodb = None

    if "generated" not in st.session_state:
        st.session_state.generated = False

    if "topic_index" not in st.session_state:
        st.session_state.topic_index = 0


def initialise_tools():
    if "db" not in st.session_state:
        st.session_state.db = db_config.connect_db(database_name="LearnLoop")

    if "db_dal" not in st.session_state:
        st.session_state.db_dal = DatabaseAccess()

    if "image_handler" not in st.session_state:
        st.session_state.image_handler = ImageHandler()

    if "openai_client" not in st.session_state:
        st.session_state.openai_client = connect_to_openai()

    if "utils" not in st.session_state:
        st.session_state.utils = Utils()

    if "blob_service_client" not in st.session_state:
        st.session_state.blob_service_client = (
            st.session_state.utils.create_blob_service_client()
        )

    if "azure_utils" not in st.session_state:
        st.session_state.azure_utils = AzureUtils()


def initialise_pages():
    if "courses_page" not in st.session_state:
        st.session_state.courses_page = CoursesOverview()

    if "lectures_page" not in st.session_state:
        st.session_state.lectures_page = LectureOverview()

    if "topics_page" not in st.session_state:
        st.session_state.topics_page = TopicOverview()

    if "theory_overview_page" not in st.session_state:
        st.session_state.theory_overview_page = TheoryOverview()

    if "socratic_dialogue_page" not in st.session_state:
        st.session_state.socratic_dialogue_page = SocraticDialogue()

    if "insights_page" not in st.session_state:
        st.session_state.insights_page = LectureInsights()

    if "quality_check_page" not in st.session_state:
        st.session_state.quality_check_page = QualityCheck()

    if "record_page" not in st.session_state:
        st.session_state.record_page = Recorder()

    if "upload_page" not in st.session_state:
        st.session_state.upload_page = UploadPage()


def qr_code_and_course_and_id_in_query_params():
    query_params = st.query_params  # Gebruik van st.query_params
    return (
        "QR_code" in query_params
        and query_params["course"] == "Plantenbiologie"
        and query_params["id"] == "f3d0f8c3-c4f5-4b9a-9b7c-7d5e6f1a2b3c"
    )


# Functie om de volgende beschikbare gebruikersnaam op te halen uit één document
def get_available_username():
    print("Getting available username for QR login...")
    users_collection = st.session_state.db.users
    # Haal het document op met alle gebruikersnamen
    user_doc = users_collection.find_one({"usernames": {"$exists": True}})
    print("User doc:", user_doc)

    if user_doc and "usernames" in user_doc:  # Check voor het 'usernames' veld
        for username, status in user_doc["usernames"].items():
            if status == "available":
                # Zet de status van deze gebruikersnaam op 'taken' zonder gebruik te maken van _id
                users_collection.update_one(
                    {
                        f"usernames.{username}": "available"
                    },  # Zoek naar de beschikbare gebruikersnaam
                    {"$set": {f"usernames.{username}": "taken"}},  # Werk de status bij
                )
                return username  # Retourneer de beschikbare gebruikersnaam
    st.error("Geen beschikbare gebruikersnamen.")
    return None


def turn_qr_code_into_username(username):
    # Sla de username op in het gewenste format {"username": username, "role": None}
    st.session_state.user_role = "student"
    st.session_state.new_username = username
    st.session_state.user_university = "Universiteit Utrecht"
    st.session_state.user_courses = ["Plantenbiologie"]
    st.session_state.user_doc = {"username": username, "role": "student"}
    save_hashed_password_account_to_database()

    st.success(f"Je bent ingelogd als {username}!")
    st.session_state.logged_in = True
    st.session_state.turned_qr_code_into_username = True
    st.query_params.clear()

    print("QR code omgezet in gebruikersnaam.")


def show_username_page(username):
    cols = st.columns([1, 1, 1])

    with cols[1]:
        st.markdown(
            "<h5 style='text-align: center; color: #00000;'>Jouw gebruikersnaam:</h5>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h1 style='text-align: center; color: #2196F3;'>{username}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color: #00000; text-align: center'>⚠️ Sla deze goed op, je hebt hem later nodig om weer in te kunnen loggen. ⚠️</p>",
            unsafe_allow_html=True,
        )

        st.text_input("Nieuw wachtwoord", type="password", key="new_password")
        st.write("\n\n")
        st.write("\n\n")

        checkbox = st.checkbox(
            "_Ik bevestig dat ik de gebruikersvoorwaarden heb gelezen en dat ik me ervan bewust ben dat LearnLoop **onafhankelijk** opereert van de universiteit, die daarom **niet** verantwoordelijk is voor mogelijke gevolgen van het gebruik van deze tool._"
        )

        # Button verschijnt alleen als checkbox is aangevinkt
        if checkbox:
            st.button(
                "**Ik ga akkoord en wil doorgaan**",
                on_click=turn_qr_code_into_username,
                args=(username,),
                use_container_width=True,
            )

        with st.expander("Gebruikersvoorwaarden", expanded=False):
            st.write("""
    **Let op: Onafhankelijk platform buiten de Universiteit**

    Welkom bij LearnLoop! Voor je verdergaat, is het belangrijk om te weten dat deze versie van LearnLoop, de *Easy-use versie*, losstaat van de universiteit. Dit platform is bedoeld voor gebruiksvriendelijke testpilots en opereert onafhankelijk van de onderwijsinstelling.

    Deze versie van LearnLoop verzamelt uitsluitend anonieme gegevens voor testdoeleinden, zoals willekeurig gegenereerde gebruikersnamen (bijv. "blueberry21"), inlogfrequenties, voortgangsdata en antwoorden van gebruikers. Alle gegevens zijn volledig geanonimiseerd en niet te herleiden naar specifieke individuen. Na afloop van de testperiode worden alle gegevens verwijderd.

    **Door een account aan te maken, bevestig je dat je begrijpt en akkoord gaat dat LearnLoop in deze versie geen officiële samenwerking met de universiteit heeft. De universiteit is daarom niet verantwoordelijk of aansprakelijk voor het gebruik van deze versie.**
    """)


def register_qr_code():
    # Controleer of de queryparameter 'QR_code' aanwezig is
    if qr_code_and_course_and_id_in_query_params():
        st.session_state.via_qr_code = True

        if not st.session_state.logged_in:
            if st.session_state.generated_username is None:
                st.session_state.generated_username = get_available_username()
            show_username_page(st.session_state.generated_username)
        else:
            st.write(
                f"Je bent al ingelogd als {st.session_state['username']['username']}."
            )
    else:
        return


def fetch_user_doc_from_db():
    print("Fetching user doc from db...")
    st.session_state.user_doc = st.session_state.db.users.find_one(
        {"username": st.session_state.user_doc["username"]}
    )


if __name__ == "__main__":
    args = get_commandline_arguments()
    # set_global_exception_handler(
    #     exception_handler, debug=args.debug
    # )

    no_login_page = args.no_login_page
    if no_login_page:
        st.session_state.logged_in = True
        st.session_state.db_name = "LearnLoop"
        st.session_state.user_doc = {"username": args.test_username, "role": "student"}
        st.session_state.selected_phase = args.run_page

    args, st.session_state.base_path = set_correct_settings_for_deployment_type()

    # Turn on 'testing' to use localhost instead of learnloop.datanose.nl for authentication
    surf_test_env = args.surf_test_env

    # Your current IP has to be accepted by Gerrit to use CosmosDB (Gerrit controls this)
    st.session_state.use_LL_cosmosdb = args.use_LL_cosmosdb
    st.session_state.use_LL_blob_storage = args.use_LL_blob_storage
    if st.session_state.use_LL_cosmosdb:
        print("LearnLoop CosmosDB is being used")
    else:
        print("UvA CosmosDB is being used")

    st.session_state.use_keyvault = args.use_keyvault

    if args.use_LL_openai_deployment:
        st.session_state.openai_model = "LLgpt-4o"
    else:
        st.session_state.openai_model = "learnloop-4o"

    # Bypass authentication when testing so flask app doesnt have to run
    # st.session_state.skip_authentication = True

    # ---------------------------------------------------------
    initialise_variables()
    initialise_tools()
    initialise_pages()

    # Give the name of the test user when one is given. If not using a test username, set to None
    if st.session_state.user_doc == {} and args.test_username is not None:
        st.session_state.user_doc = {"role": "teacher"}
        st.session_state.user_doc["username"] = args.test_username

    register_qr_code()

    if (
        st.session_state.turned_qr_code_into_username is False
        and st.session_state.via_qr_code is True
    ):
        st.stop()

    # Connect with the correct database after logging in. When rerouted to student app after SURF login, the session state is resetted
    if st.session_state.logged_in is True and st.session_state.db_switched is False:
        if st.session_state.db_name is None:
            st.session_state.db_name = "LearnLoop"

        st.session_state.db = db_config.connect_db(
            database_name=st.session_state.db_name
        )
        st.session_state.db_switched = True

    # Create a mid column with margins in which everything one a
    # page is displayed (referenced to mid_col in functions)
    left_col, mid_col, right_col = st.columns([1, 3, 1])

    if fetch_nonce_from_query() is not None:
        st.session_state.logged_in = True

    if (
        no_login_page is False
        and st.session_state.logged_in is False
        and (
            not st.session_state.user_doc
            or not st.session_state.user_doc.get("username")
        )
    ):
        print("Rendering login page")
        render_login_page()
    # Render the actual app when the user is logged in
    else:
        print("Rendering the app")

        fetch_user_doc_from_db()

        # Toggle sets this to True when the teacher wants to see the student view
        if st.session_state.student_view:
            st.session_state.user_doc["role"] = "student"

        # print(
        #     f"Logged in as {st.session_state.user_doc['username']} with user the following user doc: {st.session_state.user_doc}"
        # )

        if (
            st.session_state.modules == []
            or st.session_state.modules is None
            or st.session_state.selected_course is None
        ):
            st.session_state.modules = (
                st.session_state.db_dal.initialise_course_and_modules()
            )

        determine_username_from_nonce()
        remove_nonce_from_memories()

        check_user_doc_and_add_missing_fields()

        if st.session_state.warned is None:
            if warned := st.session_state.db_dal.fetch_if_warned() is True:
                st.session_state.warned = True
            else:
                st.session_state.warned = False

            st.session_state.db_dal.update_if_warned(warned)

        if st.session_state.selected_module is None:
            determine_selected_module()

        if st.session_state.selected_phase is None:
            st.session_state.selected_phase = "lectures"

        render_sidebar()
        render_selected_page()
