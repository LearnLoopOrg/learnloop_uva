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
import os
import argparse

# Must be called first
st.set_page_config(page_title="LearnLoop", layout="wide")

load_dotenv()


class Controller:
    def __init__(_self, args):
        _self.initialise_session_states()

        if args.use_LL_cosmosdb:
            COSMOS_URI = os.getenv("LL_COSMOS_URI")
        else:
            COSMOS_URI = os.getenv("COSMOS_URI")

        if args.use_LL_openai_deployment:
            print("Using LearnLoop OpenAI deployment")
            OPENAI_API_KEY = os.getenv("LL_OPENAI_API_KEY")
            OPENAI_API_ENDPOINT = os.getenv("LL_OPENAI_API_ENDPOINT")
            st.session_state.openai_model = "LLgpt-4o"
        else:
            print("Using UvA OpenAI deployment")
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            OPENAI_API_ENDPOINT = os.getenv("UVA_OPENAI_API_ENDPOINT")
            st.session_state.openai_model = "learnloop-4o"

        st.session_state.openai_client = connect_to_openai(
            OPENAI_API_KEY,
            OPENAI_API_ENDPOINT,  # , llm_model=st.session_state.openai_model
        )

        st.session_state.use_mongodb = True
        st.session_state.db = db_config.connect_db(COSMOS_URI)
        st.session_state.use_LL_blob_storage = args.use_LL_blob_storage

        _self.debug = True if os.getenv("DEBUG") == "True" else False

        # User
        st.session_state.username = "Luc Mahieu"

        # Data access layer
        _self.db_dal = DatabaseAccess()

        # Fetch were user left off
        st.session_state.selected_module = _self.db_dal.fetch_last_module()
        # st.session_state.selected_phase = _self.db_dal.fetch_last_phase()

        # Pages
        _self.lectures_page = LectureOverview()
        _self.courses_page = CoursesOverview()
        _self.insights_page = LectureInsights()
        _self.quality_check_page = QualityCheck()
        _self.record_page = Recorder()

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
        if "use_LL_blob_storage" not in st.session_state:
            st.session_state.use_LL_blob_storage = False

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
                    <strong>Welkom Erwin</strong>
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

    def set_selected_phase(self, phase):
        print(f"Setting phase: {phase}")
        st.session_state.selected_phase = phase
        self.db_dal.update_last_phase(phase)


def get_commandline_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

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
        "--use_LL_blob_storage",
        help="Set to True to use the LearnLoop Blob Storage instance, by default use the UvA's",
        action="store_true",
        default=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_commandline_arguments()

    if "controller" not in st.session_state:
        st.session_state.controller = Controller(args)

    st.session_state.controller.render_sidebar()
    st.session_state.controller.render_page()
