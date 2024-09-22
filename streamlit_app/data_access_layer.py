import json
import streamlit as st
import db_config as db_config
import os

class ContentAccess:
    def __init__(self):
        self.db = db_config.connect_db(st.session_state.use_mongodb) # database connection
        self.segments_list = None
        self.topics_list = None
        self.segment_index = None

    def determine_modules(self):
        """	
        Function to determine which names of modules to display in the sidebar 
        based on the JSON module files.
        """
        # Read the modules from the modules directory
        modules = os.listdir("./content/modules")

        # Remove the json extension and replace the underscores with spaces
        modules = [module.replace(".json", "").replace("_", " ") for module in modules]
        
        # Sort the modules based on the number in the name except for the practice exams
        modules.sort(key=lambda module: int(module.split(" ")[0]) if module.split(" ")[0].isdigit() else 1000)

        st.session_state.modules = modules
        
        return modules


    def get_segment_type(self, segment_index):
        return self.get_segments_list(self.get_module_name_underscored())[segment_index].get('type', None)
    
    def get_module_name_underscored(self):
        return st.session_state.selected_module.replace(' ', '_')
    
    def get_index_first_segment_in_topic(self, topic_index):
        """
        Takes in the json index of a topic and extracts the first segment in the list of 
        segments that belong to that topic.
        """
        module = st.session_state.selected_module.replace(' ', '_')
        topics = self.get_topics_list(module)
        return topics[topic_index]['segment_indexes'][0]
    
    def fetch_segment_index(self):
        """Fetch the last segment index from db"""
        # Switch the phase from overview to learning when fetching the segment index
        phase = st.session_state.selected_phase
        if phase == 'overview':
            phase = 'learning'

        user_doc = self.db.users_2.find_one({"username": st.session_state.username})
        return user_doc["progress"][st.session_state.selected_module][phase]["segment_index"]

    def get_segment_question(self, segment_index):
        return self.segments_list[segment_index].get('question', None)
        
    def get_segment_answer(self, segment_index):
        return self.segments_list[segment_index].get('answer', None)

    def get_segment_title(self, segment_index):
        return self.segments_list[segment_index]['title']
    
    def get_segment_text(self, segment_index):
        return self.segments_list[segment_index]['text']

    def get_segment_image_file_name(self, segment_index):
        return self.segments_list[segment_index].get('image', None)
        
    def get_image_path(self, image_file_name):
        return f"./content/images/{image_file_name}"

    def get_segment_mc_answers(self, segment_index):
        return self.segments_list[segment_index].get('answers', None)

    def load_page_content_of_module_in_session_state(self, module):
        file_name = self.fetch_json_file_name_of_module(module)
        path = self.generate_json_path(file_name)
        st.session_state.page_content = self.load_json_content(path)

        return st.session_state.page_content

    def fetch_json_file_name_of_module(self, module):
        return module.replace(" ", "_") + ".json"

    def generate_json_path(self, json_name):
        return f"./content/modules/{json_name}"

    def load_json_content(self, path): #TODO: This might result in a lot of memory usage, which is costly and slow
        """Load all the contents from the current JSON into memory."""
        with open(path, "r") as f:
            return json.load(f)
    
    def get_topic_segment_indexes(self, module, topic_index):
        return self.get_topics_list(module)[topic_index]['segment_indexes']

    def get_topics_list(self, module):
        """
        Each module has two types of jsons. One with the content segments and
        one that stores how the segments are divided into topics. This function
        gets the last (topics) one.
        """
        topics_json_path = f"./content/topics/{module}_topics.json"
        self.topics_list = self.load_json_content(topics_json_path)['topics']   
        return self.topics_list

    def get_segments_list(self, module):
        """
        Each module has two types of jsons. One with the content segments and
        one that stores how the segments are divided into topics. This function
        gets the first (content segments) one.
        """
        content_json_path = f"./content/modules/{module}.json"
        self.segments_list = self.load_json_content(content_json_path)['segments']
        return self.segments_list


class DatabaseAccess:
    def __init__(self):
        self.db = db_config.connect_db(st.session_state.use_mongodb)
        self.users_collection_name = 'users_2'
    
    def update_if_warned(self, boolean):
        """Callback function for a button that turns of the LLM warning message."""
        self.db.users_2.update_one(
            {"username": st.session_state.username},
            {"$set": {"warned": boolean}}
        )

    def fetch_if_warned(self):
        """Fetches from database if the user has been warned about LLM."""
        user_doc = self.db.users_2.find_one({"username": st.session_state.username})
        if user_doc is None:
            return None
        return user_doc.get("warned", None)

    def fetch_last_module(self):
        user_doc = self.find_user_doc()
        if user_doc is None:
            return None
        return user_doc.get('last_module', None)

    def update_last_module(self):
        self.db.users_2.update_one(
            {"username": st.session_state.username},
            {"$set": {"last_module": st.session_state.selected_module}}
        )

    def fetch_username_with_nonce(self):
        user_doc = self.db.users_2.find_one({'nonce': st.session_state.nonce})
        if user_doc is not None:
            st.session_state.username = user_doc['username']
        else:
            st.session_state.username = None
            print("No user found with the nonce.")

    def invalidate_nonce(self):
        self.db.users_2.update_one({'username': st.session_state.username}, {'$set': {'nonce': None}})
        st.session_state.nonce = None
        
    def fetch_all_documents(self):
        collection = self.db[self.users_collection_name]
        return list(collection.find({}))

    def find_user_doc(self):
        return self.db.users_2.find_one({"username": st.session_state.username})

    def fetch_progress_counter(self, module, user_doc):
        module = module.replace('_', ' ')
        progress_counter = user_doc.get('progress', {}).get(module, {}).get('learning', {}).get('progress_counter', None)
        return progress_counter
    
    def update_progress_counter_for_segment(self, module, new_progress_count):
        self.db.users_2.update_one(
            {"username": st.session_state.username},
            {"$set": {f"progress.{module}.learning.progress_counter.{str(st.session_state.segment_index)}": new_progress_count}}
        )

    def add_progress_counter(self, module, empty_dict):
        """
        Add the json to the database that contains the count of how
        many times the user answered a certain question.
        """
        self.db.users_2.update_one(
            {"username": st.session_state.username}, 
            {"$set": {f"progress.{module}.learning.progress_counter": empty_dict}}
        )  