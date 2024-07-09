from datetime import timedelta
import json
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
from pymongo.server_api import ServerApi
import streamlit as st
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from PIL import Image

from api.module import ModuleRepository
from utils.db_config import connect_db
import base64

load_dotenv()


class Utils:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.module_repository = ModuleRepository(
            connect_db(st.session_state.use_mongodb)
        )

    def upload_file_to_blob_storage(self, container_name, source_path, blob_name):
        """
        Upload a file to a specific directory within a container in Azure Blob Storage.

        """

        try:
            container_client = self.blob_service_client.create_container(container_name)
            print(f"Container '{container_name}' created successfully.")
        except Exception as e:
            print(f"Container might already exist: {e}")

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        with open(source_path, "rb") as data:
            blob_client.upload_blob(data)
        print(
            f"File '{source_path}' uploaded to '{blob_name}' in container '{container_name}'."
        )

    def upload_content_to_blob_storage(self, container_name, blob_name, content):
        """
        Upload content to a specific directory within a container in Azure Blob Storage.

        """

        try:
            container_client = self.blob_service_client.create_container(container_name)
            print(f"Container '{container_name}' created successfully.")
        except Exception as e:
            print(f"Container might already exist: {e}")

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        blob_client.upload_blob(content, overwrite=True)
        print(f"Content uploaded to '{blob_name}' in container '{container_name}'.")

    @st.cache_data(ttl=timedelta(hours=4))
    def download_content_from_blob_storage(_self, container_name, blob_name):
        """
        Download content from a specific directory within a container in Azure Blob Storage.

        """
        # Get a BlobClient for the blob
        blob_client = _self.blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        # Download the content of the blob
        try:
            blob_data = blob_client.download_blob().readall()
            print(
                f"Content downloaded from '{blob_name}' in container '{container_name}'."
            )
            return blob_data
        except Exception as e:
            print(f"Failed to download blob: {e}")
            return None

    def toggle_button(self, segment_id):
        if st.session_state["button_state" + segment_id] == "no":
            st.session_state["button_state" + segment_id] = "yes"
        else:
            st.session_state["button_state" + segment_id] = "no"

    def save_st_change(self, key1, key2):
        st.session_state[key1] = st.session_state[key2]

    def list_to_enumeration(self, list_input):
        enumeration_output = ""
        for count, elem in enumerate(list_input):
            enumeration_output += f"{str(count+1)}) {elem}\n"
        return enumeration_output

    def enumeration_to_list(self, enumeration_input):
        list_output = enumeration_input.split("\n")
        list_output = [x.split(")", 1)[1].strip() for x in list_output if x != ""]
        return list_output

    @st.cache_data(ttl=timedelta(hours=4))
    def original_topics(self, module) -> list:
        data_modules = self.download_content_from_blob_storage(
            "content", f"topics/{module}.json"
        )
        data_modules = json.loads(data_modules)
        topics = data_modules["topics"]
        return topics

    @st.cache_data(ttl=timedelta(hours=4))
    def original_segments(_self, module) -> list:
        data_modules = _self.module_repository.get_content_from_db(module)
        return data_modules["original_lecturepath_content"]["segments"]

    def key_func(self, k):
        return k["segment_id"]

    def preprocessed_segments(self, module) -> list:
        # outputs a list of dictionaries with detele:yes or delete:no tags.
        original_segments_list = self.original_segments(module)
        segments_list = []
        session_state_dict = {k: v for k, v in st.session_state.items()}
        for key, value in session_state_dict.items():
            composite_key = str(key).split("-")
            if composite_key[0] == "new":
                segment_id = int(composite_key[1])
                segment = {}
                segment["segment_id"] = segment_id
                static_segment = original_segments_list[segment_id]
                if static_segment["type"] == "theory":
                    segment["text"] = value
                elif static_segment["type"] == "question" and len(composite_key) == 2:
                    segment["question"] = value
                elif static_segment["type"] == "question" and len(composite_key) == 3:
                    segment["answer"] = value
                elif static_segment["type"] == "question" and len(composite_key) == 4:
                    segment["answers"] = {}
                    if composite_key[3] == "correct_answer":
                        segment["answers"]["correct_answer"] = value
                    elif composite_key[3] == "wrong_answers":
                        segment["answers"]["wrong_answers"] = self.enumeration_to_list(
                            value
                        )
                segments_list.append(segment)
        segments_list = sorted(segments_list, key=self.key_func)
        new_segments_list = original_segments_list
        for segment_id, segment in enumerate(new_segments_list):
            if segment["type"] == "theory":
                new_segments_list[segment_id]["text"] = [
                    x for x in segments_list if x["segment_id"] == segment_id
                ][0]["text"]
            elif segment["type"] == "question":
                new_segments_list[segment_id]["question"] = [
                    x
                    for x in segments_list
                    if x["segment_id"] == segment_id and "question" in x
                ][0]["question"]
                if "answer" in segment:
                    new_segments_list[segment_id]["answer"] = [
                        x
                        for x in segments_list
                        if x["segment_id"] == segment_id and "answer" in x
                    ][0]["answer"]
                elif "answers" in segment:
                    new_segments_list[segment_id]["correct_answer"] = [
                        x
                        for x in segments_list
                        if x["segment_id"] == segment_id
                        and x.get("answers") is not None
                        and "correct_answer" in x.get("answers")
                    ][0]["answers"]["correct_answer"]
                    new_segments_list[segment_id]["wrong_answers"] = [
                        x
                        for x in segments_list
                        if x["segment_id"] == segment_id
                        and x.get("answers") is not None
                        and "wrong_answers" in x.get("answers")
                    ][0]["answers"]["wrong_answers"]

            new_segments_list[segment_id]["delete"] = session_state_dict[
                "button_state" + str(segment_id)
            ]
        return new_segments_list


class ImageHandler:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.container_name = None
        self.blob_name = None

    @st.cache_data(ttl=timedelta(hours=4))
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
        try:
            self.get_image_url(segment)
            image = self.download_image_from_blob_storage()
            if max_height:
                image = self.resize_image_to_max_height(image, max_height)

            st.image(image)
        except:
            st.error("No image found for this segment.")
