from datetime import timedelta
import json
import streamlit as st
import utils.db_config as db_config
from typing import List
from models.uni_database import Course, CourseCatalog, Lecture


class DatabaseAccess:
    def __init__(self):
        self.db = db_config.connect_db(
            st.session_state.use_LL_cosmosdb
        )  # database connection
        self.users_collection_name = "users"
        self.segments_list = None
        self.topics_list = None
        self.segment_index = None

    @st.cache_data(ttl=timedelta(hours=4))
    def determine_modules(_self):
        """
        Function to determine which names of modules to display in the sidebar
        based on the names in the database of the university.
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
        modules = [module for module in modules]

        # Sort the modules based on the number in the name except for the practice exams
        modules.sort(
            key=lambda module: int(module.split("_")[0])
            if module.split("_")[0].isdigit()
            else 1000
        )

        st.session_state.modules = modules

        return modules

    def initialise_modules(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.get_course_catalog()
        if st.session_state.selected_course is None:
            st.session_state.selected_course = course_catalog.courses[0].title

        return [
            module.title
            for module in self.get_lectures_for_course(
                st.session_state.selected_course, course_catalog
            )
        ]

    def get_course_catalog(
        self, university_name: str = "Universiteit van Amsterdam"
    ) -> CourseCatalog:
        """
        Load the course catalog from the (dummy) university database.
        """
        data = self.db.courses.find_one({"university_name": university_name})
        print(f"Data (courses doc): {data}")

        courses = [
            Course(
                title=course["title"],
                description=course["description"],
                lectures=[
                    Lecture(title=lecture["title"], description=lecture["description"])
                    for lecture in course["lectures"]
                ],
            )
            for course in data["courses"]
        ]

        return CourseCatalog(courses=courses)

    def get_lectures_for_course(
        self, selected_course: str, catalog: CourseCatalog
    ) -> List[Lecture]:
        """
        Get the lectures for a given course from the course catalog.
        """
        for course in catalog.courses:
            if course.title == selected_course:
                return course.lectures

    def get_segment_type(self, segment_index):
        return self.get_segments_list_from_db(st.session_state.selected_module)[
            segment_index
        ].get("type", None)

    def get_index_last_visited_segment_in_topic(self, topic_index: int) -> int:
        """
        Takes in the json index of a topic and extracts the first segment in the list of
        segments that belong to that topic.
        """
        module = st.session_state.selected_module
        topics = self.get_topics_list_from_db(module)
        user_doc = self.find_user_doc()
        segment_indices: int | None = (
            user_doc.get("progress", {})
            .get(module, {})
            .get("learning", {})
            .get("last_visited_segment_index_per_topic_index", [])
        )

        if not segment_indices:
            self.db.users.update_one(
                {"username": st.session_state.username},
                {
                    "$set": {
                        f"progress.{st.session_state.selected_module}.learning.last_visited_segment_index_per_topic_index": [
                            topics[i]["segment_indexes"][0]
                            for i, _ in enumerate(topics)
                        ]
                    }
                },
            )
            return topics[topic_index]["segment_indexes"][0]
        else:
            return (
                segment_indices[topic_index]
                if len(segment_indices) > topic_index
                else 0
            )

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
        page_content = self.db.content.find_one({"lecture_name": module})
        return page_content["corrected_lecturepath_content"] if page_content else None

    def fetch_module_topics(self, module):
        page_content = self.db.content.find_one({"lecture_name": module})
        return page_content["corrected_lecturepath_topics"]

    def get_lecture(self, lecture_name):
        return self.db.content.find_one({"lecture_name": lecture_name})

    def get_image_path(self, image_file_name):
        return f"src/data/content/images/{image_file_name}"

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
    def get_segments_list_from_db(_self, module):
        query = {"lecture_name": module}
        doc = _self.db.content.find_one(query)

        if doc and "corrected_lecturepath_content" in doc:
            _self.segments_list = doc["corrected_lecturepath_content"]["segments"]
        else:
            _self.segments_list = None

        return _self.segments_list

    @st.cache_data(ttl=timedelta(hours=4))
    def get_topics_list_from_db(_self, module):
        query = {"lecture_name": module}
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

    def get_progress_counter(self, module, user_doc) -> dict:
        progress_counter = (
            user_doc.get("progress", {})
            .get(module, {})
            .get("learning", {})
            .get("progress_counter", None)
        )
        return progress_counter if progress_counter is not None else {}

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

    def update_module_status(self, status):
        """
        Update the status of the module, such as 'not_recorded', 'generated', 'corrected' etc.
        """
        self.db.content.update_one(
            {"lecture_name": st.session_state.selected_module},
            {"$set": {"status": status}},
        )

    def fetch_module_status(self):
        """
        Fetches if the module has been generated and checked on quality by teacher.
        """
        return self.db.content.find_one(
            {"lecture_name": st.session_state.selected_module}
        )["status"]
