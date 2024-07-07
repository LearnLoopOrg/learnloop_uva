from datetime import timedelta
import json
import streamlit as st
import utils.db_config as db_config


class DatabaseAccess:
    def __init__(self):
        self.db = db_config.connect_db(
            st.session_state.use_mongodb
        )  # database connection
        self.users_collection_name = "users"
        self.segments_list = None
        self.topics_list = None
        self.segment_index = None

    @st.cache_data(ttl=timedelta(hours=4))
    def determine_modules(_self):
        """
        Function to determine which names of modules to display in the sidebar
        based on the JSON module files.
        """
        # Read the modules from the modules directory
        modules = []
        lectures = _self.db.content.find()
        for lecture in lectures:
            try:
                modules.append(lecture["lecture_name"])
            except KeyError:
                print("No lecture_name key found in the document.")
                continue

        # Remove the json extension and replace the underscores with spaces
        modules = [module.replace("_", " ") for module in modules]

        print(f"\n\nmodules: {modules}\n\n")
        # Sort the modules based on the number in the name except for the practice exams
        modules.sort(
            key=lambda module: int(module.split(" ")[0])
            if module.split(" ")[0].isdigit()
            else 1000
        )

        st.session_state.modules = modules

        print(f"\n\nmodules: {modules}\n\n")

        return modules

    def get_segment_type(self, segment_index):
        return self.get_segments_list_from_db(self.get_module_name_underscored())[
            segment_index
        ].get("type", None)

    def get_module_name_underscored(self):
        return st.session_state.selected_module.replace(" ", "_")

    def get_index_first_segment_in_topic(self, topic_index):
        """
        Takes in the json index of a topic and extracts the first segment in the list of
        segments that belong to that topic.
        """
        module = st.session_state.selected_module.replace(" ", "_")
        topics = self.get_topics_list_from_db(module)
        return topics[topic_index]["segment_indexes"][0]

    def fetch_segment_index(self):
        """Fetch the last segment index from db"""
        # Switch the phase from overview to learning when fetching the segment index
        phase = st.session_state.selected_phase
        if phase == "topics":
            phase = "learning"

        user_doc = self.db.users.find_one({"username": st.session_state.username})
        return user_doc["progress"][st.session_state.selected_module][phase][
            "segment_index"
        ]

    def get_segment_question(self, segment_index):
        return self.segments_list[segment_index].get("question", None)

    def get_segment_answer(self, segment_index):
        return self.segments_list[segment_index].get("answer", None)

    def get_segment_image_file_name(self, segment_index):
        return self.segments_list[segment_index].get("image", None)

    def get_segment_mc_answers(self, segment_index):
        return self.segments_list[segment_index].get("answers", None)

    def fetch_module_content(self, module):
        page_content = self.db.content.find_one(
            {"lecture_name": module.replace(" ", "_")}
        )
        return page_content["corrected_lecturepath_content"]

    def fetch_module_topics(self, module):
        page_content = self.db.content.find_one(
            {"lecture_name": module.replace(" ", "_")}
        )
        return page_content["corrected_lecturepath_topics"]

    def get_image_path(self, image_file_name):
        return f"src/data/content/images/{image_file_name}"

    def fetch_json_file_name_of_module(self, module):
        return module.replace(" ", "_") + ".json"

    def generate_json_path(self, json_name):
        return f"src/data/content/modules/{json_name}"

    @st.cache_data(ttl=timedelta(hours=4))
    def load_json_content(
        self, path
    ):  # TODO: This might result in a lot of memory usage, which is costly and slow
        """Load all the contents from the current JSON into memory."""
        with open(path, "r") as f:
            return json.load(f)

    def get_topic_segment_indexes(_self, module, topic_index):
        return _self.get_topics_list_from_db(module)[topic_index]["segment_indexes"]

    @st.cache_data(ttl=timedelta(hours=4))
    def fetch_courses(self):
        """
        Determines which courses are available for this student by querying
        the database of the university.
        """
        # TODO: This is a placeholder for the actual implementation
        return [
            (
                "AI & Data Science",
                "Leer over de toepassing van AI in bedrijfsstrategieën en -operaties en verdiep je in de fundamenten van AI. ",
            ),
            (
                "Business Analytics",
                "Leer hoe je data kunt analyseren en visualiseren om er waardevolle inzichten uit te halen en beslissingen te ondersteunen.",
            ),
            (
                "Ethical AI",
                "Leer over de ethische implicaties van AI en hoe je AI-projecten kunt ontwerpen en implementeren op een ethisch verantwoorde en duurzame manier.",
            ),
        ]

    @st.cache_data(ttl=timedelta(hours=4))
    def fetch_lectures(_self):
        """
        Determines which lectures are available for this student for the given course
        by querying the database of the university.
        """
        # TODO: This is a placeholder for the actual implementation
        return [
            (
                "1_Embryonale_ontwikkeling",
                "De ontwikkeling van een embryo van bevruchting tot geboorte en de invloed van externe factoren.",
            ),
            (
                "2_Machine_Learning",
                "De fundamentele principes achter machine learning en hoe je die kunt implementern om bedrijfsprocessen te verbeteren.",
            ),
            (
                "3_Data_analytics",
                "Hoe je data kunt analyseren en visualiseren om er waardevolle inzichten uit te halen en beslissingen te ondersteunen.",
            ),
            (
                "4_Data_engineering",
                "Hoe je data pipelines kunt bouwen om data te verzamelen en te verwerkem van verschillende bronnen op grote schaal.",
            ),
        ]

    @st.cache_data(ttl=timedelta(hours=4))
    def get_segments_list_from_db(_self, module):
        query = {"lecture_name": module.replace(" ", "_")}
        doc = _self.db.content.find_one(query)

        print("\n\nDocument keys:", doc.keys(), "\n\n")

        if doc and "corrected_lecturepath_content" in doc:
            _self.segments_list = doc["corrected_lecturepath_content"]["segments"]
        else:
            _self.segments_list = None

        return _self.segments_list

    def get_topics_list_from_db(_self, module):
        query = {"lecture_name": module.replace(" ", "_")}
        doc = _self.db.content.find_one(query)

        if doc and "corrected_lecturepath_topics" in doc:
            _self.topics_list = doc["corrected_lecturepath_topics"]["topics"]
        else:
            _self.topics_list = None

        return _self.topics_list

    def update_if_warned(self, boolean):
        """Callback function for a button that turns of the LLM warning message."""
        self.db.users.update_one(
            {"username": st.session_state.username}, {"$set": {"warned": boolean}}
        )

    def fetch_if_warned(self):
        """Fetches from database if the user has been warned about LLM."""
        user_doc = self.db.users.find_one({"username": st.session_state.username})
        if user_doc is None:
            return None
        return user_doc.get("warned", None)

    def fetch_last_module(self):
        user_doc = self.find_user_doc()
        if user_doc is None:
            return None
        return user_doc.get("last_module", None)

    def update_last_module(self):
        self.db.users.update_one(
            {"username": st.session_state.username},
            {"$set": {"last_module": st.session_state.selected_module}},
        )

    def fetch_info(self):
        user_doc = self.db.users.find_one({"nonce": st.session_state.nonce})
        if user_doc is not None:
            st.session_state.username = user_doc["username"]
            st.session_state.courses = user_doc["courses"]
        else:
            st.session_state.username = None
            print("No user found with the nonce.")

    def invalidate_nonce(self):
        self.db.users.update_one(
            {"username": st.session_state.username}, {"$set": {"nonce": None}}
        )
        st.session_state.nonce = None

    def fetch_all_documents(self):
        collection = self.db[self.users_collection_name]
        return list(collection.find({}))

    def find_user_doc(self):
        return self.db.users.find_one({"username": st.session_state.username})

    def fetch_progress_counter(self, module, user_doc):
        module = module.replace("_", " ")
        progress_counter = (
            user_doc.get("progress", {})
            .get(module, {})
            .get("learning", {})
            .get("progress_counter", None)
        )
        return progress_counter

    def update_progress_counter_for_segment(self, module, new_progress_count):
        self.db.users.update_one(
            {"username": st.session_state.username},
            {
                "$set": {
                    f"progress.{module}.learning.progress_counter.{str(st.session_state.segment_index)}": new_progress_count
                }
            },
        )

    def add_progress_counter(self, module, empty_dict):
        """
        Add the json to the database that contains the count of how
        many times the user answered a certain question.
        """
        self.db.users.update_one(
            {"username": st.session_state.username},
            {"$set": {f"progress.{module}.learning.progress_counter": empty_dict}},
        )

    def fetch_last_phase(self):
        """
        Fetches the phase that the user last visited, such as 'courses', 'practice' etc.
        """
        user_doc = self.find_user_doc()
        return user_doc["last_phase"]

    def update_last_phase(self, phase):
        """
        Update the last phase the user visitied, such as 'courses', 'practice' etc.
        """
        self.db.users.update_one(
            {"username": st.session_state.username}, {"$set": {"last_phase": phase}}
        )
