import streamlit as st
from PIL import Image
from io import BytesIO
from azure.storage.blob import BlobServiceClient
import os
from data.data_access_layer import DatabaseAccess
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class Utils:
    def __init__(self):
        self.db_dal = DatabaseAccess()

    def add_spacing(self, count):
        for _ in range(count):
            st.write("\n\n")

    def set_phase_to_match_lecture_status(self, phase):
        """
        Determines which lecture page to display based on the selected lecture status,
        which indicates if a lecture is recorded, generated or corrected.
        """

        if st.session_state.db.content.find_one(
            {"lecture_name": st.session_state.selected_module}
        ):
            status = self.db_dal.fetch_module_status()

            if status == "generated":
                st.session_state.selected_phase = "generated"
            elif status == "corrected":
                st.session_state.selected_phase = phase
            else:
                st.session_state.selected_phase = "not_recorded"


class ImageHandler:
    def __init__(self):
        if st.session_state.use_keyvault:
            self.connection_string = AzureUtils.get_secret(
                "AZURE-BLOB-STORAGE-CONNECTION-STRING", "lluniappkv"
            )
        else:
            self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.container_name = None
        self.blob_name = None

    # @st.cache_data(ttl=timedelta(hours=4)) #TODO: cache messes up the image rendering, only rendering the first image.
    def download_image_from_blob_storage(_self) -> Image.Image:
        blob_client = _self.blob_service_client.get_blob_client(
            container=_self.container_name, blob=_self.blob_name
        )
        blob_data = blob_client.download_blob().readall()
        return Image.open(BytesIO(blob_data))

    def get_image_url(self, segment):
        self.container_name = "uva-celbiologie"
        self.blob_name = segment.get("image", {}).get("url")

    def resize_image_to_max_height(self, image: Image.Image, max_height):
        # Calculate the new width maintaining the aspect ratio
        aspect_ratio = image.width / image.height
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

        # Resize the image
        resized_img = image.resize((new_width, new_height))

        return resized_img

    def render_image(self, segment, max_height=None):
        self.get_image_url(segment)
        try:
            image = self.download_image_from_blob_storage()
            if max_height:
                image = self.resize_image_to_max_height(image, max_height)

            st.image(image)
        # Afbeelding niet gevonden
        except Exception:
            pass


class AzureUtils:
    @staticmethod
    def get_secret(secret_name: str, key_vault_name: str) -> str:
        """
        Returns a secret from Azure Key Vault.
        """
        key_vault_uri = f"https://{key_vault_name}.vault.azure.net"

        credential = DefaultAzureCredential()

        client = SecretClient(vault_url=key_vault_uri, credential=credential)

        retrieved_secret = client.get_secret(secret_name)

        return retrieved_secret.value
