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
                "Upload geslaagd! Geef een naam aan de module en klik op 'Genereer module' om de module te genereren."
            )

            with st.form(key="generate_learning_path"):
                module_name = st.text_input(
                    # "Naam van module", value=uploaded_file.name, key="username"
                    "Naam van module",
                    "...",
                    key="username",
                )
                submit_button = st.form_submit_button("Genereer module")
                # TODO: Implementeer de post request naar de backend om de module te genereren
                if submit_button:
                    print(f"""
                            Uitvoeren van post request naar backend om module te genereren met blob name: uploaded_materials/{uploaded_file.name} en module name: {module_name}.
                            """)
                    st.success(
                        f'Module \'{module_name}\' wordt gegenereerd; het leertraject zal binnen enkele minuten onder "Mijn vakken" > "Kies module"s verschijnen.'
                    )

    ## Gebruik deze code om de post request te sturen naar de backend om de module te genereren.
    # def show_spinner_till_generated(self):
    #     with st.spinner("Oefenmaterialen worden gegenereerd..."):
    #         url = "https://contentpipeline.azurewebsites.net/contentpipeline?code=YxHEt2ZBmN6YX912nsC_i9KVpof7RVlr3k1yMSmZXlajAzFu_xvH1w=="
    #         params = {
    #             "lecture": "celbio_3",
    #             "run_full_pipeline": "true",
    #             "upload_to_demo_db": "true",
    #         }
    #         print(f"Sending http request to: {url} with params: {params}")
    #         # requests.get(url, params=params)
    #         while st.session_state.generated is False:
    #             status = self.db_dal.fetch_module_status()
    #             if status == "generated":
    #                 st.session_state.generated = True
    #             time.sleep(1)  # Sleep to avoid overwhelming the database with requests
