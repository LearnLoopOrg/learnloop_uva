import streamlit as st
from utils.utils import Utils
from io import BytesIO
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
        leerdoelen: str,
        output_language: str,
    ):
        try:
            params = {
                "input_file_name": input_file_name,
                "module_name": module_name,
                "course_name": course_name,
                "description": description,
                "output_language": output_language,
                "leerdoelen": leerdoelen,
            }

            response = requests.get(self.api_url, params=params)

            if response.status_code == 200:
                return True, "Pipeline succesvol gestart"
            else:
                error_message = response.text
                return False, f"Error bij het starten van de pipeline: {error_message}"

        except requests.exceptions.RequestException as e:
            return False, f"Connectie error: {str(e)}"

    def run(self):
        st.title(self.title)
        # if st.button("Trigger CP"):
        #     self.trigger_content_pipeline(
        #         input_file_name="state_of_ai_report.mp4",
        #         module_name="test",
        #         course_name="test",
        #         output_language="dutch",
        #     )
        uploaded_file = st.file_uploader("Kies een bestand", type=["mp4"])
        if uploaded_file is not None:
            # Initialiseer de voortgangsbalk en statusbericht
            self.progress_bar = st.progress(0)
            self.progress_text = st.empty()
            uploaded_file.name = uploaded_file.name.replace("MP4", "mp4")
            # Upload het bestand met de voortgangscallback
            self.utils.upload_content_to_blob_storage(
                self.container_name,
                f"uploaded_materials/{uploaded_file.name}",
                uploaded_file.getvalue(),
                progress_callback=self.progress_callback,
            )

            st.success(
                f"Upload geslaagd van {uploaded_file.name}! Geef een naam aan de module en klik op 'Genereer module' om de module te genereren."
            )

            with st.form(key="generate_learning_path"):
                module_name = st.text_input(
                    "Naam van module",
                    key="module_name",
                )
                # Get the courses that belong to this user
                course_name = st.selectbox(
                    "Cursus",
                    options=st.session_state.user_doc["courses"],
                    key="course_name",
                )
                output_language = st.selectbox(
                    "Selecteer taal",
                    options=["Nederlands", "English"],
                    key="language",
                )
                description = st.text_input("Beschrijving", key="description")
                leerdoelen = st.text_area("Leerdoelen", key="leerdoelen")
                output_language = (
                    "dutch" if output_language == "Nederlands" else "english"
                )

                submit_button = st.form_submit_button(
                    "Creëer module", use_container_width=True
                )

                if submit_button:
                    if not module_name:
                        st.error("Gelieve een modulenaam in te vullen.")
                    elif not course_name:
                        st.error("Gelieve een cursus te selecteren.")
                    else:
                        print(
                            f"Uitvoeren van post request naar backend om module te genereren met blob name uploaded_materials/{uploaded_file.name} en module {module_name} (beschrijving: {description} in course {course_name} met output_language {output_language}."
                        )
                        if description == "":
                            description = ""
                        self.trigger_content_pipeline(
                            input_file_name=uploaded_file.name,
                            module_name=module_name,
                            course_name=course_name,
                            description=description,
                            leerdoelen=leerdoelen,
                            output_language=output_language,
                        )
                        st.success(
                            f'Module \'{module_name}\' wordt gegenereerd; het leertraject zal binnen enkele minuten onder "Mijn vakken" > "Kies module"s verschijnen.'
                        )


if __name__ == "__main__":
    upload_page = UploadPage()
    upload_page.trigger_content_pipeline(
        input_file_name="state_of_ai_report.mp4",
        module_name="test",
        course_name="test",
        output_language="dutch",
    )
