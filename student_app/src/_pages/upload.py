import streamlit as st
from utils.utils import Utils
from io import BytesIO


class UploadPage:
    def __init__(self):
        self.utils = Utils()
        self.container_name = "uu-demo"
        self.title = "Creëer module"
        self.progress_bar = None
        self.progress_text = None

    def progress_callback(self, bytes_transferred, total_bytes):
        progress = int(bytes_transferred / total_bytes * 100)
        self.progress_bar.progress(min(progress, 100))
        self.progress_text.write(f"{progress}% geüpload")

    def run(self):
        st.title(self.title)

        uploaded_file = st.file_uploader("Kies een bestand", type=["mp4"])
        if uploaded_file is not None:
            # Initialiseer de voortgangsbalk en statusbericht
            self.progress_bar = st.progress(0)
            self.progress_text = st.empty()

            # Upload het bestand met de voortgangscallback
            self.utils.upload_content_to_blob_storage(
                self.container_name,
                f"uploaded_materials/{uploaded_file.name}",
                uploaded_file.getvalue(),
                progress_callback=self.progress_callback,
            )

            st.success(
                "Upload geslaagd! Je bestand wordt verwerkt en je ontvangt een notificatie wanneer het module klaar is."
            )

            with st.form(key="generate_learning_path"):
                st.text_input("Naam van module", value=uploaded_file.name, key="name")
