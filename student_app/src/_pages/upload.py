import streamlit as st
from utils.utils import Utils
import streamlit as st
from azure.storage.blob import BlobServiceClient
from io import BytesIO
import os


class UploadPage:
    def __init__(self):
        self.utils = Utils()
        blob_connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            blob_connection_string
        )
        self.container_name = "uu-demo"
        self.title = "Upload Pagina"

    # def upload_to_blob(self, file):
    #     # Generate blob name from file name
    #     blob_client = self.blob_service_client.get_blob_client(
    #         container=self.container_name, blob=f"uploaded_materials/{file.name}"
    #     )
    #     # Upload file content
    #     blob_client.upload_blob(file, overwrite=True)
    #     return blob_client.url

    def run(self):
        st.title(self.title)
        st.write(
            "Upload hier je college om verwerkt te laten worden tot een leertraject."
        )

        uploaded_file = st.file_uploader("Kies een bestand", type=["mp4"])
        if uploaded_file is not None:
            with st.spinner("Je bestand wordt geüpload..."):
                self.utils.upload_content_to_blob_storage(
                    "uu-demo", f"uploaded_materials/{uploaded_file.name}", uploaded_file
                )
                st.success(
                    "Je bestand is geüpload en zal weldra beschikbaar komen als leertraject! Waneer het verwerkt is zal dit te zien zijn in de lijst van leertrajecten."
                )
