import json
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
from pymongo.server_api import ServerApi
import streamlit as st

load_dotenv()

class Utils:
    def __init__(self):
        self.db = self.config_db()

    @st.cache_resource(show_spinner=False)
    def config_db(_self, use_mongodb=True):
        """
        Connect to either MongoDB or CosmosDB and ping to check connection.
        """
        if not use_mongodb:
            COSMOS_URI = os.getenv('COSMOS_URI')
            db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())
        else:
            MONGO_URI = os.getenv('MONGO_DB')
            db_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())

        db = db_client.UvA_NAF

        # Ping database to check if it's connected
        try:
            db.command("ping")
            print("Connected to database")
        except Exception as e:
            print(f"Error: {e}")

        return db


    def save_st_change(self, key1, key2):
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

    def original_segments_list(self, module):
        with open(f'src/data/content/modules/{module}.json') as f:
            data_modules = json.load(f)
        segments = data_modules['segments']
        return segments

    def key_func(self, k):
        return k["segment_id"]


    def upload_json(self, module):
        original_segments = self.original_segments_list(module)
        segments_list = []
        session_state_dict = {k: v for k, v in st.session_state.items() if "button" not in k}
        for key, value in session_state_dict.items():
            composite_key = key.split("-")
            if composite_key[0]=="new":
                segment_id = int(composite_key[1])
                segment = {}
                segment["segment_id"] = segment_id
                static_segment = original_segments[segment_id] 
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
        data = { "module_name": "NAF_1",
                "status": "corrected",
                "segments": original_segments}
        for segment_id, segment in enumerate(data["segments"]):
            if segment["type"]== "theory":
                data["segments"][segment_id]["text"] = [ x for x in segments_list if x["segment_id"] == segment_id ][0]["text"]
            elif segment["type"] == "question":
                data["segments"][segment_id]["question"] = [x for x in segments_list if x["segment_id"] == segment_id and "question" in x][0]["question"]
                if "answer" in segment:
                    data["segments"][segment_id]["answer"] = [x for x in segments_list if x["segment_id"] == segment_id and "answer" in x][0]["answer"]
                elif "answers" in segment:
                    data["segments"][segment_id]["correct_answer"] = [x for x in segments_list if x["segment_id"] == segment_id and x.get("answers") is not None and "correct_answer" in x.get("answers")][0]["answers"]["correct_answer"]
                    data["segments"][segment_id]["wrong_answers"] = [x for x in segments_list if x["segment_id"] == segment_id and  x.get("answers") is not None and "wrong_answers" in x.get("answers")][0]["answers"]["wrong_answers"]
    
        # Upload the updated json file to database
        if self.db.content.find_one({"module_name": "NAF_1"}):
            self.db.content.update_one({"module_name": "NAF_1"}, {"$set": {"segments": data["segments"]}})
        else:
            self.db.content.insert_one(data)

        with open(f"src/data/content/modules/{module}_updated.json",'w', encoding='utf-8') as f:
            json.dump( data , f, ensure_ascii=False, indent=4)



