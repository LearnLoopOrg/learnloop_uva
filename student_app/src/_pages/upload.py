import streamlit as st
from utils.utils import Utils
import requests
import time


class UploadPage:
    def __init__(self):
        self.utils = Utils()
        self.container_name = "uu-demo"
        self.title = "Creëer module"
        self.progress_bar = None
        self.progress_text = None
        self.api_url = "https://learnloopcontentpipeline.azurewebsites.net/api/contentpipelinehttp?code=8zG4ThuDDpzez8v46xyBvpR7iGWElTurc8Hzx4GgTKeyAzFumB3U7A=="
        # self.api_url = "http://localhost:7071/api/contentpipelinehttp?code=8zG4ThuDDpzez8v46xyBvpR7iGWElTurc8Hzx4GgTKeyAzFumB3U7A=="

    def progress_callback(self, bytes_transferred, total_bytes):
        progress = int(bytes_transferred / total_bytes * 100)
        self.progress_bar.progress(min(progress, 100))
        self.progress_text.write(f"{progress}% geüpload")

    def trigger_content_pipeline(
        self,
        input_file_name: str,
        module_name: str,
        course_name: str,
        description: str,
        learning_objectives: str,
        output_language: str,
    ):
        try:
            params = {
                "input_file_name": input_file_name,
                "module_name": module_name,
                "course_name": course_name,
                "description": description,
                "output_language": output_language,
                "learning_objectives": learning_objectives,
            }

            response = requests.get(self.api_url, params=params)

            if response.status_code == 200:
                return True, "Pipeline succesvol gestart"
            else:
                error_message = response.text
                return False, f"Error bij het starten van de pipeline: {error_message}"

        except requests.exceptions.RequestException as e:
            return False, f"Connectie error: {str(e)}"

    def go_to_module_quality_check(self, phase):
        st.session_state.selected_phase = phase
        st.session_state.selected_module = st.session_state.module_name
        st.session_state.db_dal.update_last_phase(phase)

    def display_eta_progress(self):
        if not st.session_state.generation_progress_started:
            st.session_state.generation_progress_started = True
            # Simulate generation progress bar
            file_size_mb = len(st.session_state.uploaded_file.getvalue()) / (
                1024 * 1024
            )
            estimated_seconds_per_mb = 1  # seconds per MB
            estimated_time = file_size_mb * estimated_seconds_per_mb
            progress_bar = st.progress(0)
            progress_text = st.empty()
            for i in range(int(estimated_time)):
                time.sleep(1)
                progress = int((i + 1) / estimated_time * 100)
                progress_bar.progress(progress)
                remaining_time = estimated_time - (i + 1)
                remaining_minutes, remaining_seconds = divmod(remaining_time, 60)
                progress_text.write(
                    f"Geschatte resterende tijd: {remaining_minutes:.0f} minuten en {remaining_seconds:.0f} seconden"
                )
            progress_bar.progress(100)
            progress_text.write("Module gegenereerd!")
            progress_bar.empty()
            progress_text.empty()
            st.session_state.module_generated = True
            st.rerun()

    def initialise_session_state(self):
        # Initialize session state variables
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = None
        if "upload_complete" not in st.session_state:
            st.session_state.upload_complete = False
        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False
        if "module_generated" not in st.session_state:
            st.session_state.module_generated = False
        if "generation_progress_started" not in st.session_state:
            st.session_state.generation_progress_started = False

        # Initialize form-related session state variables
        if "module_name" not in st.session_state:
            st.session_state.module_name = ""
        if "course_name" not in st.session_state:
            st.session_state.course_name = ""
        if "output_language" not in st.session_state:
            st.session_state.output_language = ""
        if "module_description" not in st.session_state:
            st.session_state.module_description = ""
        if "learning_objectives" not in st.session_state:
            st.session_state.learning_objectives = ""

    def display_example_input_format(self):
        cols = st.columns([1, 2])
        with cols[0]:
            st.write(
                "Upload een video zoals een collegeopname of kennisclip waarbij de slides duidelijk te zien zijn zoals in onderstaande voorbeeld."
            )
        with cols[0]:
            st.image(
                "src/data/example_input_format_video.png", use_container_width=True
            )

    def reset_page(self):
        st.session_state.uploaded_file = None
        st.session_state.upload_complete = False
        st.session_state.form_submitted = False
        st.session_state.module_generated = False
        st.session_state.generation_progress_started = False
        st.session_state.module_name = ""
        st.session_state.course_name = ""
        st.session_state.output_language = ""
        st.session_state.module_description = ""
        st.session_state.learning_objectives = ""
        st.session_state.uploaded_file_name = ""

    def run(self):
        st.title(self.title)

        self.initialise_session_state()

        self.display_example_input_format()

        uploaded_file = st.file_uploader("Kies een bestand", type=["mp4"])

        # Display the form
        if not st.session_state.form_submitted and uploaded_file is not None:
            self.display_module_creation_form()
        elif st.session_state.form_submitted:
            # Display submitted data
            self.display_submitted_data()
            if not st.session_state.module_generated:
                self.display_eta_progress()
            else:
                st.button(
                    "🔎 Bekijk nieuwe module",
                    use_container_width=True,
                    on_click=self.go_to_module_quality_check,
                    args=("quality-check",),
                )
                st.button(
                    "➕ Genereer nieuwe module",
                    use_container_width=True,
                    on_click=self.reset_page,
                )

        if uploaded_file is not None and st.session_state.upload_complete is False:
            st.session_state.uploaded_file = uploaded_file
            self.handle_file_upload(uploaded_file)

    def handle_file_upload(self, uploaded_file):
        # Show upload progress bar
        self.progress_bar = st.progress(0)
        self.progress_text = st.empty()

        # Begin upload
        uploaded_file.name = uploaded_file.name.replace("MP4", "mp4")
        self.utils.upload_content_to_blob_storage(
            self.container_name,
            f"uploaded_materials/{uploaded_file.name}",
            uploaded_file.getvalue(),
            progress_callback=self.progress_callback,
        )

        # Upload complete
        st.session_state.upload_complete = True
        # Clear the progress bar
        self.progress_bar.empty()
        self.progress_text.empty()
        st.session_state.uploaded_file_name = uploaded_file.name

    def display_module_creation_form(self):
        with st.form(key="generate_learning_path"):
            st.text_input("Naam van module", key="module_name_input")
            st.selectbox(
                "Cursus",
                options=st.session_state.user_doc["courses"],
                key="course_name_input",
            )
            st.selectbox(
                "Selecteer taal",
                options=["Nederlands", "English"],
                key="output_language_input",
            )
            st.text_input("Beschrijving", key="module_description_input")
            st.text_area("Leerdoelen", key="learning_objectives_input")

            if st.session_state.upload_complete:
                submit_button = st.form_submit_button(
                    "Creëer module", use_container_width=True
                )
                if submit_button:
                    st.session_state.form_submitted = True
                    st.session_state.module_name = st.session_state.module_name_input
                    st.session_state.course_name = st.session_state.course_name_input
                    st.session_state.output_language = (
                        st.session_state.output_language_input
                    )
                    st.session_state.module_description = (
                        st.session_state.module_description_input
                    )
                    st.session_state.learning_objectives = (
                        st.session_state.learning_objectives_input
                    )
                    self.handle_form_submission()
                    st.rerun()
            else:
                st.form_submit_button(
                    "Creëer module",
                    use_container_width=True,
                    disabled=True,
                )
                st.info("Na het uploaden van de video kun je de module creëren.")

    def handle_form_submission(self):
        if not st.session_state.module_name:
            st.error("Gelieve een modulenaam in te vullen.")
        elif not st.session_state.course_name:
            st.error("Gelieve een cursus te selecteren.")
        else:
            st.session_state.module_submitted = True
            # Hide any previous messages or progress bars
            self.progress_bar.empty()
            self.progress_text.empty()
            # Trigger content pipeline
            self.trigger_content_pipeline(
                input_file_name=st.session_state.uploaded_file_name,
                module_name=st.session_state.module_name,
                course_name=st.session_state.course_name,
                description=st.session_state.module_description,
                learning_objectives=st.session_state.learning_objectives,
                output_language=st.session_state.output_language,
            )

    def display_submitted_data(self):
        # Display the form data as static text
        st.header("Module informatie")
        st.write(f"**Naam van module:** {st.session_state.module_name}")
        st.write(f"**Cursus:** {st.session_state.course_name}")
        st.write(f"**Taal:** {st.session_state.output_language}")
        st.write(f"**Beschrijving:** {st.session_state.module_description}")
        st.write(f"**Leerdoelen:** {st.session_state.learning_objectives}")
