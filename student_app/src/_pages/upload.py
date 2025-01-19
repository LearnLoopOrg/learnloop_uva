import streamlit as st
from utils.utils import Utils
import requests
import time
from moviepy.editor import VideoFileClip
import io
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadPage:
    def __init__(self):
        self.utils = Utils()
        self.container_name = "uu-demo"
        self.title = "Creëer module"
        self.progress_bar = None
        self.progress_text = None
        self.api_url = "https://contentpipeline.azurewebsites.net/api/orchestrators/{filename}?code=0HFCNUo8wBNrO5uesJeLNpc_wDqFaBkO-CNOew5QCRNEAzFuQaSzXw%3D%3D"
        # self.api_url = "https://learnloopcontentpipeline.azurewebsites.net/api/contentpipelinehttp?code=8zG4ThuDDpzez8v46xyBvpR7iGWElTurc8Hzx4GgTKeyAzFumB3U7A=="
        # self.api_url = "http://localhost:7071/api/contentpipelinehttp?code=8zG4ThuDDpzez8v46xyBvpR7iGWElTurc8Hzx4GgTKeyAzFumB3U7A=="

    def progress_callback(self, bytes_transferred, total_bytes):
        progress = int(bytes_transferred / total_bytes * 100)
        self.progress_bar.progress(min(progress, 100))
        self.progress_text.write(f"{progress}% geüpload")

    def go_to_module_quality_check(self, phase):
        st.session_state.selected_phase = phase
        st.session_state.selected_module = st.session_state.module_name
        self.db_dal.update_last_phase(phase)

    def get_video_duration(self):
        # Direct BytesIO object gebruiken van de upload
        video_bytes = io.BytesIO(st.session_state.uploaded_file.getvalue())
        with VideoFileClip(video_bytes) as video:
            return video.duration

    def display_eta_progress(self):
        if not st.session_state.generation_progress_started:
            st.session_state.generation_progress_started = True

            # ======= HARDCODED VIDEO DURATION BECAUSE get_video_duration() DOESN'T WORK =========
            # video_duration = self.get_video_duration()
            video_duration = 5400  # seconden = 1,5 uur
            # ====================================================================================

            video_duration_minutes = video_duration / 60  # duur in minuten
            estimated_seconds_per_video_minute = 14  # seconden per minuut video
            estimated_time = int(
                video_duration_minutes * estimated_seconds_per_video_minute
            )

            # Initialize progress bar
            progress_bar = st.progress(0)
            progress_text = st.empty()

            st.session_state.module_generated = False
            for i in range(estimated_time):
                time.sleep(1)
                progress = int((i + 1) / estimated_time * 100)
                progress_bar.progress(progress)
                remaining_time = estimated_time - (i + 1)
                remaining_minutes, remaining_seconds = divmod(remaining_time, 60)
                progress_text.write(
                    f"Geschatte resterende tijd: {remaining_minutes:.0f} minuten en {remaining_seconds:.0f} seconden"
                )
                st.session_state.selected_module = st.session_state.module_name
                status = self.db_dal.fetch_module_status()
                if status == "generated":
                    st.session_state.module_generated = True
                    break
                if st.session_state.pipeline_error:
                    st.error(st.session_state.pipeline_error)
                    break
            if st.session_state.module_generated:
                progress_bar.progress(100)
                progress_text.write("Module gegenereerd!")
                progress_bar.empty()
                progress_text.empty()
                st.rerun()
            else:
                progress_bar.progress(100)
                with st.spinner("Nog even geduld, de module is bijna klaar..."):
                    while st.session_state.module_generated is False:
                        status = self.db_dal.fetch_module_status()
                        if status == "generated":
                            st.session_state.module_generated = True
                            st.success("De module is gegenereerd!")
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
                        time.sleep(1)

    def initialise_session_state(self):
        # Initialize session state variables
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = None
        if "upload_complete" not in st.session_state:
            st.session_state.upload_complete = False
        if "requested_form_submission" not in st.session_state:
            st.session_state.requested_form_submission = False
        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False
        if "module_generated" not in st.session_state:
            st.session_state.module_generated = False
        if "generation_progress_started" not in st.session_state:
            st.session_state.generation_progress_started = False
        if "pipeline_triggered" not in st.session_state:
            st.session_state.pipeline_triggered = False
        if "pipeline_error" not in st.session_state:
            st.session_state.pipeline_error = None

        # Initialize form-related session state variables with default values
        if "module_name_input" not in st.session_state:
            st.session_state.module_name_input = ""
        if "course_name_input" not in st.session_state:
            courses = st.session_state.user_doc.get("courses", [])
            st.session_state.course_name_input = courses[0] if courses else ""
        if "output_language_input" not in st.session_state:
            st.session_state.output_language_input = "Nederlands"  # Default value
        if "module_description_input" not in st.session_state:
            st.session_state.module_description_input = ""
        if "learning_objectives_input" not in st.session_state:
            st.session_state.learning_objectives_input = ""

    def display_example_input_format(self):
        cols = st.columns([1, 2])
        with cols[0]:
            st.write(
                "Upload een video zoals een collegeopname of kennisclip waarbij de slides duidelijk te zien zijn zoals in onderstaande voorbeeld."
            )
        with cols[0]:
            st.image("src/data/example_input_format_video.png")

    def reset_page(self):
        logger.info("Resetting page state")
        # Reset all session state variables
        keys_to_reset = [
            "uploaded_file",
            "upload_complete",
            "form_submitted",
            "module_generated",
            "generation_progress_started",
            "requested_form_submission",
            "pipeline_triggered",
            "pipeline_error",
            "module_name",
            "course_name",
            "output_language",
            "module_description",
            "learning_objectives",
            "module_name_input",
            "course_name_input",
            "output_language_input",
            "module_description_input",
            "learning_objectives_input",
        ]

        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]

        logger.info("Page state reset completed")
        st.rerun()

    def run(self):
        self.db_dal = st.session_state.db_dal
        st.title(self.title)

        self.initialise_session_state()

        # Add upload new file button if there's already a file uploaded
        if st.session_state.uploaded_file is not None:
            if st.button("⬅️ Upload nieuwe file", type="primary"):
                self.reset_page()
            st.divider()

        self.display_example_input_format()

        st.session_state.uploaded_file = st.file_uploader(
            "Kies een bestand", type=["mp4", "txt"]
        )

        # Display the form
        if st.session_state.uploaded_file is not None:
            if (
                not st.session_state.form_submitted
                and not st.session_state.module_generated
                and st.session_state.requested_form_submission is False
            ):
                self.display_module_creation_form()

            elif st.session_state.requested_form_submission:
                self.handle_form_submission()
                # Display submitted data
                if st.session_state.form_submitted:
                    self.display_submitted_data()
                    # Add option to upload new file after form submission
                    if st.button("⬅️ Upload andere file", type="primary"):
                        self.reset_page()
                if not st.session_state.module_generated:
                    self.display_eta_progress()

            # else:
            #     st.success("De module is gegenereerd!")
            #     st.button(
            #         "🔎 Bekijk nieuwe module",
            #         use_container_width=True,
            #         on_click=self.go_to_module_quality_check,
            #         args=("quality-check",),
            #     )
            #     st.button(
            #         "➕ Genereer nieuwe module",
            #         use_container_width=True,
            #         on_click=self.reset_page,
            #     )

            if st.session_state.upload_complete is False:
                self.handle_file_upload()

    def handle_file_upload(self):
        logger.info(f"Starting file upload for: {st.session_state.uploaded_file.name}")
        # Show upload progress bar
        self.progress_bar = st.progress(0)
        self.progress_text = st.empty()

        # Begin upload
        st.session_state.uploaded_file.name = (
            st.session_state.uploaded_file.name.replace("MP4", "mp4")
        )
        logger.info(
            f"Uploading file to blob storage: {st.session_state.uploaded_file.name}"
        )
        self.utils.upload_content_to_blob_storage(
            self.container_name,
            f"uploaded_materials/{st.session_state.uploaded_file.name}",
            st.session_state.uploaded_file.getvalue(),
            progress_callback=self.progress_callback,
        )
        # Upload complete
        logger.info("File upload completed successfully")
        st.session_state.upload_complete = True
        # Clear the progress bar
        self.progress_bar.empty()
        self.progress_text.empty()
        st.rerun()

    def set_requested_form_submission_true(self):
        st.session_state.requested_form_submission = True

    def display_module_creation_form(self):
        st.header("Module informatie")

        with st.form("generate_learning_path", clear_on_submit=False):
            st.text_input("Naam van module", key="module_name_input")

            # Ensure courses exist in user_doc before using them
            courses = st.session_state.user_doc.get("courses", [])
            if courses:
                st.selectbox(
                    "Cursus",
                    options=courses,
                    key="course_name_input",
                    index=0
                    if "course_name_input" not in st.session_state
                    else courses.index(st.session_state.course_name_input),
                )
            else:
                st.error("Geen cursussen gevonden. Neem contact op met de beheerder.")
                return

            st.selectbox(
                "Selecteer taal",
                options=["Nederlands", "English"],
                key="output_language_input",
                index=0
                if "output_language_input" not in st.session_state
                else ["Nederlands", "English"].index(
                    st.session_state.output_language_input
                ),
            )

            st.text_input("Beschrijving", key="module_description_input")
            st.text_area("Leerdoelen", key="learning_objectives_input")

            if st.session_state.upload_complete:
                submitted = st.form_submit_button(
                    "Creëer module",
                    use_container_width=True,
                    on_click=self.set_requested_form_submission_true,
                )
                if submitted:
                    st.success("Video is succesvol geüpload!")
            else:
                st.form_submit_button(
                    "Creëer module",
                    use_container_width=True,
                    disabled=True,
                )
                st.info(
                    "De video wordt nog geüpload. Zodra dit klaar is, kun je de module maken."
                )

    def identify_missing_fields(self):
        missing_fields = []
        if not st.session_state.module_name_input:
            missing_fields.append("de **modulenaam**")
        if not st.session_state.course_name_input:
            missing_fields.append("de **cursus**")
        if not st.session_state.output_language_input:
            missing_fields.append("de **taal van de module**")
        if not st.session_state.module_description_input:
            missing_fields.append("de **beschrijving**")

        if missing_fields:
            return missing_fields
        else:
            return None

    def warn_about_missing_fields(self, missing_fields):
        if len(missing_fields) > 1:
            missing_fields_text = (
                ", ".join(missing_fields[:-1]) + " en " + missing_fields[-1]
            )
        else:
            missing_fields_text = missing_fields[0]
        st.warning(f"Vul nog {missing_fields_text} in om de module te kunnen creëren.")

    def trigger_content_pipeline_thread(
        self,
        input_file_name: str,
        module_name: str,
        course_name: str,
        description: str,
        learning_objectives: str,
        output_language: str,
    ):
        try:
            logger.info(
                f"Preparing to trigger content pipeline for file: {input_file_name}"
            )

            # Construct base URL with filename
            formatted_url = self.api_url.format(filename=input_file_name)
            logger.info(f"Using API URL: {formatted_url}")

            # Create JSON payload instead of query parameters
            payload = {
                "input_file_name": input_file_name,
                "module_name": module_name,
                "course_name": course_name,
                "module_description": description,
                "output_language": output_language,
                "learning_objectives": learning_objectives,
            }
            logger.info(f"Making API request with payload: {payload}")

            # Make POST request with JSON payload
            response = requests.post(formatted_url, json=payload)
            response.raise_for_status()

            logger.info(f"Content pipeline response: {response.text}")
            logger.info("Content pipeline triggered successfully")
            st.session_state.pipeline_triggered = True
        except requests.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            logger.error(
                f"Response content: {e.response.text if hasattr(e, 'response') else 'No response content'}"
            )
            st.session_state.pipeline_error = error_msg

    def handle_form_submission(self):
        if missing_fields := self.identify_missing_fields():
            logger.warning(f"Form submission failed - missing fields: {missing_fields}")
            self.warn_about_missing_fields(missing_fields)
            st.session_state.form_submitted = False
        else:
            logger.info("Processing form submission")
            st.session_state.module_name = st.session_state.module_name_input
            st.session_state.course_name = st.session_state.course_name_input
            st.session_state.output_language = st.session_state.output_language_input
            st.session_state.module_description = (
                st.session_state.module_description_input
            )
            st.session_state.learning_objectives = (
                st.session_state.learning_objectives_input
            )

            # Hide any previous messages or progress bars
            if self.progress_bar:
                self.progress_bar.empty()
            if self.progress_text:
                self.progress_text.empty()

            # Start de API-aanroep in een aparte thread
            logger.info("Starting content pipeline thread")
            st.session_state.pipeline_error = None
            st.session_state.pipeline_triggered = False
            threading.Thread(
                target=self.trigger_content_pipeline_thread,
                args=(
                    st.session_state.uploaded_file.name,
                    st.session_state.module_name,
                    st.session_state.course_name,
                    st.session_state.module_description,
                    st.session_state.learning_objectives,
                    st.session_state.output_language,
                ),
                daemon=True,
            ).start()

            st.session_state.form_submitted = True
            logger.info("Form submission completed successfully")

    def display_submitted_data(self):
        # Display the form data as static text
        st.header("Module informatie")
        st.write(f"**Naam van module:** {st.session_state.module_name}")
        st.write(f"**Cursus:** {st.session_state.course_name}")
        st.write(f"**Taal:** {st.session_state.output_language}")
        st.write(f"**Beschrijving:** {st.session_state.module_description}")

        if st.session_state.learning_objectives == "":
            st.write("**Leerdoelen:** Geen leerdoelen meegegeven")
        else:
            st.write(f"**Leerdoelen:** {st.session_state.learning_objectives}")
