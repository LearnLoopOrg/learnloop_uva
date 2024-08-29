from utils.openai_client import connect_to_openai
from utils.utils import AzureUtils
import streamlit as st
from dotenv import load_dotenv
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess
from _pages.lecture_overview import LectureOverview
from _pages.course_overview import CoursesOverview
from _pages.lecture_student_answers_insights import LectureInsights
from _pages.lecture_quality_check import QualityCheck
from _pages.record_lecture import Recorder
from _pages.login import Login
import os

# Must be called first
st.set_page_config(page_title="LearnLoop", layout="wide")

load_dotenv()


class Controller:
    def __init__(_self):
        _self.initialise_session_states()

        # DEMO: Use Azure KeyVault
        st.session_state.use_keyvault = True

        # Get keys from the keyvault
        if st.session_state.use_keyvault:
            LL_AZURE_OPENAI_API_KEY = AzureUtils.get_secret(
                "LL-AZURE-OPENAI-API-KEY", "lluniappkv"
            )
            LL_AZURE_OPENAI_API_ENDPOINT = AzureUtils.get_secret(
                "LL-AZURE-OPENAI-API-ENDPOINT", "lluniappkv"
            )
            MONGO_URI = AzureUtils.get_secret("MONGO-URI", "lluniappkv")
        else:
            LL_AZURE_OPENAI_API_KEY = os.getenv("LL_AZURE_OPENAI_API_KEY")
            LL_AZURE_OPENAI_API_ENDPOINT = os.getenv("LL_AZURE_OPENAI_API_ENDPOINT")
            MONGO_URI = os.getenv("MONGO_URI")

        st.session_state.openai_client = connect_to_openai(
            LL_AZURE_OPENAI_API_KEY, LL_AZURE_OPENAI_API_ENDPOINT, llm_model="LLgpt-4o"
        )

        st.session_state.use_mongodb = True
        st.session_state.db = db_config.connect_db(MONGO_URI)

        _self.debug = True if os.getenv("DEBUG") == "True" else False

        # Username
        # st.session_state.username = "Luc Mahieu"
        st.session_state.username = None

        # Data access layer
        _self.db_dal = DatabaseAccess()

        # Showing login page for testing purposes
        _self.no_login_page = False

        # Fetch were user left off
        st.session_state.selected_module = _self.db_dal.fetch_last_module()
        # st.session_state.selected_phase = _self.db_dal.fetch_last_phase()
        # print(f"Selected phase: {st.session_state.selected_phase}")

        # Pages
        _self.lectures_page = LectureOverview()
        _self.courses_page = CoursesOverview()
        _self.insights_page = LectureInsights()
        _self.quality_check_page = QualityCheck()
        _self.record_page = Recorder()
        _self.login_page = Login()

    def initialise_session_states(self):
        if "selected_course" not in st.session_state:
            st.session_state.selected_course = None
        if "selected_phase" not in st.session_state:
            st.session_state.selected_phase = "courses"
        if "selected_module" not in st.session_state:
            st.session_state.selected_module = None
        if "openai_client" not in st.session_state:
            st.session_state.openai_client = None
        if "use_mongodb" not in st.session_state:
            st.session_state.use_mongodb = None
        if "username" not in st.session_state:
            st.session_state.username = None
        if "db" not in st.session_state:
            st.session_state.db = None
        if "generated" not in st.session_state:
            st.session_state.generated = False
        if "use_keyvault" not in st.session_state:
            st.session_state.use_keyvault = False

    def render_page(self):
        """
        Determines what type of page to display based on which module the user selected.
        """
        match st.session_state.selected_phase:
            case "courses":
                self.courses_page.run()
            case "lectures":
                self.lectures_page.run()
            case "record":
                self.record_page.run()
            case "quality_check":
                self.quality_check_page.run()
            case "insights":
                self.insights_page.run()
            case "login":
                self.login_page.run()
            case _:  # Show courses by default
                self.courses_page.run()

    def render_sidebar(self):
        with st.sidebar:
            st.image(
                "src/data/images/logo.png",
                use_column_width=False,
                width=150,
            )

            st.markdown(
                """
                <style>
                    .closer-line {
                        margin-top: -5px;
                    }
                </style>

                <h1> 
                    <strong>Welkom Björn</strong>
                </h1>
                <hr class="closer-line">
            """,
                unsafe_allow_html=True,
            )
            st.button(
                "📚 Mijn vakken",
                on_click=self.set_selected_phase,
                args=("courses",),
                use_container_width=True,
            )
            # st.button(
            #     "⚙️ Instellingen",
            #     on_click=self.set_selected_phase,
            #     args=("courses",),
            #     use_container_width=True,
            # )
            # st.button(
            #     "💬 Ondersteuning",
            #     on_click=self.set_selected_phase,
            #     args=("courses",),
            #     use_container_width=True,
            # )

            # st.subheader("👤 Remko Offringa")

    def set_selected_phase(self, phase):
        print(f"Setting phase: {phase}")
        st.session_state.selected_phase = phase
        self.db_dal.update_last_phase(phase)

    def determine_username_from_nonce(self):
        """
        Fetches the username from the database using the nonce in the query parameters.
        """
        st.session_state.nonce = (
            self.fetch_nonce_from_query()
        )  # ? Why save nonce in session state? Pass a param?
        self.db_dal.fetch_info()

    def remove_nonce_from_memories(self):
        """Removes the nonce from the query parameters and session state."""
        st.query_params.pop("nonce", None)
        self.db_dal.invalidate_nonce()
        st.session_state.nonce = None

    def fetch_nonce_from_query(self):
        return st.query_params.get("nonce", None)


if __name__ == "__main__":
    if "controller" not in st.session_state:
        st.session_state.controller = Controller()

    controller = st.session_state.controller
    # Directly after logging in via SURF, the nonce is fetched from the query parameters
    if controller.fetch_nonce_from_query() is not None:
        # The username is fetched from the database with this nonce
        controller.determine_username_from_nonce()
        # The nonce is removed from the query params, the session state and the database
        controller.remove_nonce_from_memories()

    if (
        st.session_state.controller.no_login_page is False
        and controller.fetch_nonce_from_query() is None
        and st.session_state.username is None
    ):
        st.session_state.selected_phase = "login"
        st.session_state.controller.render_page()
    else:
        st.session_state.controller.render_sidebar()
        st.session_state.controller.render_page()
