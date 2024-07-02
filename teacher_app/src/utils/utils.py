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

load_dotenv()

class Utils:
    def __init__(self):
        self.connection_string = os.getenv('AZURE_BLOB_STORAGE_KEY')
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)


    def upload_content_to_blob_storage(self, container_name, blob_name, content):
        """
        Upload content to a specific directory within a container in Azure Blob Storage.

        """

        try:
            container_client = self.blob_service_client.create_container(container_name)
            print(f"Container '{container_name}' created successfully.")
        except Exception as e:
            print(f"Container might already exist: {e}")

        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        blob_client.upload_blob(content, overwrite=True)
        print(f"Content uploaded to '{blob_name}' in container '{container_name}'.")

    def download_content_from_blob_storage(self, container_name, blob_name):
        """
        Download content from a specific directory within a container in Azure Blob Storage.

        """
        # Get a BlobClient for the blob
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Download the content of the blob
        try:
            blob_data = blob_client.download_blob().readall()
            print(f"Content downloaded from '{blob_name}' in container '{container_name}'.")
            return blob_data
        except Exception as e:
            print(f"Failed to download blob: {e}")
            return None
    
    def download_image_from_blob_storage(self, container_name, blob_name):
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_data = blob_client.download_blob().readall()
        return Image.open(BytesIO(blob_data))

    def toggle_button(self, segment_id):
        if st.session_state['button_state'+segment_id] == 'no':
            st.session_state['button_state'+segment_id] = 'yes'
        else:
            st.session_state['button_state'+segment_id] = 'no'

    def save_st_change(self, key1,key2):
        st.session_state[key1] = st.session_state[key2]

    def list_to_enumeration(self, list_input):
        enumeration_output = ""
        for count, elem in enumerate(list_input):
            enumeration_output+= f"{str(count+1)}) {elem}\n"
        return enumeration_output

    def enumeration_to_list(self, enumeration_input):
        list_output = enumeration_input.split("\n")
        list_output = [ x.split(')', 1)[1].strip() for x in list_output if x!="" ]
        return list_output

    def original_topics(self, module) -> list:
        data_modules = self.download_content_from_blob_storage( "content", f"topics/{module}.json" )
        data_modules = json.loads(data_modules)
        topics = data_modules['topics']
        return topics

    def original_segments(self, module) -> list:
        data_modules = self.download_content_from_blob_storage( "content", f"modules/{module}.json" )
        data_modules = json.loads(data_modules)
        segments = data_modules['segments']
        return segments

    def key_func(self, k):
        return k["segment_id"]

    def preprocessed_segments(self, module) -> list:
        # outputs a list of dictionaries with detele:yes or delete:no tags.
        original_segments_list = self.original_segments(module)
        segments_list = []
        session_state_dict = {k: v for k, v in st.session_state.items()}
        for key, value in session_state_dict.items():
            composite_key = key.split("-")
            if composite_key[0]=="new":
                segment_id = int(composite_key[1])
                segment = {}
                segment["segment_id"] = segment_id
                static_segment = original_segments_list[segment_id] 
                if static_segment["type"]== "theory":
                    segment["text"] = value
                elif static_segment["type"] == "question" and len(composite_key)==2:
                    segment["question"] = value
                elif static_segment["type"] == "question" and len(composite_key)==3:
                    segment["answer"] = value
                elif static_segment["type"] == "question" and len(composite_key)==4:
                    segment["answers"] = {}
                    if composite_key[3] == "correct_answer":
                        segment["answers"]["correct_answer"] = value
                    elif composite_key[3] == "wrong_answers":
                        segment["answers"]["wrong_answers"] = self.enumeration_to_list(value)
                segments_list.append(segment)
        segments_list  = sorted(segments_list, key=self.key_func)
        new_segments_list =  original_segments_list
        for segment_id, segment in enumerate(new_segments_list):
            if segment["type"]== "theory":
                new_segments_list[segment_id]["text"] = [ x for x in segments_list if x["segment_id"] == segment_id ][0]["text"]
            elif segment["type"] == "question":
                new_segments_list[segment_id]["question"] = [x for x in segments_list if x["segment_id"] == segment_id and "question" in x][0]["question"]
                if "answer" in segment:
                    new_segments_list[segment_id]["answer"] = [x for x in segments_list if x["segment_id"] == segment_id and "answer" in x][0]["answer"]
                elif "answers" in segment:
                    new_segments_list[segment_id]["correct_answer"] = [x for x in segments_list if x["segment_id"] == segment_id and x.get("answers") is not None and "correct_answer" in x.get("answers")][0]["answers"]["correct_answer"]
                    new_segments_list[segment_id]["wrong_answers"] = [x for x in segments_list if x["segment_id"] == segment_id and  x.get("answers") is not None and "wrong_answers" in x.get("answers")][0]["answers"]["wrong_answers"]
            
            new_segments_list[segment_id]["delete"] = session_state_dict["button_state"+str(segment_id)]
        return new_segments_list



    def upload_modules_json(self, module, segments_list) -> None:
        modules_data = {"module_name": "NAF_1", "updated":"yes"}
        modules_segments_list = []

        for segment in segments_list:
            if segment["delete"] == "no":
                modules_segment = segment.copy()
                del modules_segment["delete"]
                modules_segments_list.append(modules_segment)
        
        modules_data["segments"] = modules_segments_list
        json_modules_data = json.dumps(modules_data)
        self.upload_content_to_blob_storage( "content-corrected", f"modules/{module}.json", json_modules_data)
    
    def upload_modules_topics_json(self, module, segments_list) -> None:
        modules_topics_data = { "module_name": "NAF_1", "updated":"yes"}
        modules_topics_topics_list= []

        data_modules_topics = self.download_content_from_blob_storage( "content", f"topics/{module}.json" )
        data_modules_topics = json.loads(data_modules_topics)

        topics = data_modules_topics['topics']
        topic_id = 0
        topic_segment_id = 0
        topic_segment_id_new = 0
        topic_segment_id_list= []

        for segment in segments_list:
            topic_title = topics[topic_id]["topic_title"]
            if segment["delete"] == "no":
                topic_segment_id_list.append(topic_segment_id_new)
                topic_segment_id_new += 1

            if topic_segment_id == len(topics[topic_id]["segment_indexes"])-1:
                modules_topics_topics_list.append( 
                    {"topic_title":topic_title,
                    "segment_indexes":  topic_segment_id_list} )
                topic_id += 1
                topic_segment_id = 0
                topic_segment_id_list = []
            else:
                topic_segment_id += 1

        modules_topics_data["topics"] = modules_topics_topics_list
        json_modules_topics_data = json.dumps(modules_topics_data)
        self.upload_content_to_blob_storage( "content-corrected", f"topics/{module}.json", json_modules_topics_data)






