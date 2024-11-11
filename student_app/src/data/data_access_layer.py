from datetime import timedelta
import datetime
import json
import streamlit as st
import utils.db_config as db_config
from typing import List
from models.uni_database import Course, CourseCatalog, Lecture


class DatabaseAccess:
    def __init__(self):
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
        lectures = st.session_state.db.content.find()
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

    def initialise_course_and_modules(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.get_course_catalog(
            st.session_state.user_doc["university"],
            st.session_state.user_doc["courses"],
        )
        if st.session_state.selected_course is None:
            st.session_state.selected_course = course_catalog.courses[0].title

        return [
            module.title
            for module in self.get_lectures_for_course(
                st.session_state.selected_course, course_catalog
            )
        ]

    def get_course_catalog(
        self,
        university_name: str = "Universiteit van Amsterdam",
        user_courses: List[str] = None,
    ) -> CourseCatalog:
        """
        Load the course catalog from the university database,
        filtered by university and user's selected courses.
        """
        data = st.session_state.db.courses.find_one(
            {"university_name": university_name}
        )

        # Filter courses based on user_courses
        if user_courses:
            filtered_courses = [
                course for course in data["courses"] if course["title"] in user_courses
            ]
        else:
            filtered_courses = data["courses"]

        courses = [
            Course(
                title=course["title"],
                description=course["description"],
                lectures=[
                    Lecture(
                        title=lecture["title"],
                        description=lecture["description"],
                    )
                    for lecture in course["lectures"]
                ],
            )
            for course in filtered_courses
        ]

        return CourseCatalog(courses=courses)

    def get_lectures_for_course(
        self, selected_course: str, catalog: CourseCatalog
    ) -> List[Lecture]:
        """
        Get the lectures for a given course from the course catalog.
        """
        for course in catalog.courses:
            if course.title.lower() == selected_course.lower():
                return course.lectures

    def get_segment_type(self, segment_index):
        return self.get_segments_list_from_db(st.session_state.selected_module)[
            segment_index
        ].get("type", None)

    def get_index_first_segment_in_topic(self, topic_index):
        """
        Takes in the json index of a topic and extracts the first segment in the list of
        segments that belong to that topic.
        """
        module = st.session_state.selected_module
        topics = self.get_topics_list_from_db(module)
        return topics[topic_index]["segment_indexes"][0]

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
            st.session_state.db.users.update_one(
                {"username": st.session_state.username["name"]},
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

        user_doc = st.session_state.db.users.find_one(
            {"username": st.session_state.username["name"]}
        )
        return user_doc["progress"][st.session_state.selected_module][phase][
            "segment_index"
        ]

    def get_segment_question(self, segment_index):
        return self.segments_list[segment_index].get("question", None)

    def get_segment_answer(self, segment_index):
        return self.segments_list[segment_index].get("answer", None)

    def get_segment_title(self, segment_index):
        return self.segments_list[segment_index]["title"]

    def get_segment_text(self, segment_index):
        return self.segments_list[segment_index]["text"]

    def get_segment_image_file_name(self, segment_index):
        return self.segments_list[segment_index].get("image", None)

    def get_image_path(self, image_file_name):
        return f"src/data/content/images/{image_file_name}"

    def get_segment_mc_answers(self, segment_index):
        return self.segments_list[segment_index].get("answers", None)

    def get_topic_questions(self, module, topic_segment_indexes):
        """
        Retrieves the question segments for a given module and topic.

        Args:
            module (str): The module name.
            topic_segment_indexes (list): List of segment indexes for the topic.

        Returns:
            dict: A dictionary containing the question segments, where the keys are the segment indexes and the values are the segment data.
        """
        content_segments = self.get_segments_list_from_db(module)
        question_segments = {}

        for index in topic_segment_indexes:
            if content_segments[index]["type"] == "question":
                question_segments[index] = content_segments[index]

        return question_segments

    def fetch_question(self, module, segment_index):
        query = {f"progress.{module}.feedback.questions.segment_index": segment_index}
        # projection = {f'progress.{module}.feedback.questions.score': 1, '_id': 0}

        results = st.session_state.db.users.find(query)

        return results

    def fetch_module_content(self, module):
        page_content = st.session_state.db.content.find_one({"lecture_name": module})
        return page_content["corrected_lecturepath_content"] if page_content else None

    def fetch_original_module_content(self, module):
        page_content = st.session_state.db.content.find_one({"lecture_name": module})
        if page_content and "original_lecturepath_content" in page_content:
            return page_content["original_lecturepath_content"]
        else:
            return None

    def fetch_corrected_module_content(self, module):
        page_content = st.session_state.db.content.find_one({"lecture_name": module})
        if page_content and "corrected_lecturepath_content" in page_content:
            return page_content["corrected_lecturepath_content"]
        else:
            return None

    def fetch_module_topics(self, module):
        page_content = st.session_state.db.content.find_one({"lecture_name": module})
        return page_content["corrected_lecturepath_topics"]

    def generate_json_path(self, json_name):
        return f"src/data/content/modules/{json_name}"

    @st.cache_data(ttl=datetime.timedelta(hours=4))
    def load_json_content(
        _self, path
    ):  # TODO: This might result in a lot of memory usage, which is costly and slow
        """Load all the contents from the current JSON into memory."""
        with open(path, "r") as f:
            return json.load(f)

    def get_topic_segment_indexes(_self, module, topic_index):
        return _self.get_topics_list_from_db(module)[topic_index]["segment_indexes"]

    @st.cache_data(ttl=timedelta(hours=4))
    def get_segments_list_from_db(_self, module):
        query = {"lecture_name": module}
        doc = st.session_state.db.content.find_one(query)

        if doc and "corrected_lecturepath_content" in doc:
            _self.segments_list = doc["corrected_lecturepath_content"]["segments"]
        else:
            _self.segments_list = None

        return _self.segments_list

    @st.cache_data(ttl=timedelta(hours=4))
    def get_topics_list_from_db(_self, module):
        query = {"lecture_name": module}
        doc = st.session_state.db.content.find_one(query)

        if doc and "corrected_lecturepath_topics" in doc:
            _self.topics_list = doc["corrected_lecturepath_topics"]["topics"]
        else:
            _self.topics_list = None

        return _self.topics_list

    def update_if_warned(self, boolean):
        """Callback function for a button that turns of the LLM warning message."""
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]},
            {"$set": {"warned": boolean}},
        )

    def fetch_if_warned(self):
        """Fetches from database if the user has been warned about LLM."""
        user_doc = st.session_state.db.users.find_one(
            {"username": st.session_state.username["name"]}
        )
        if user_doc is None:
            return None
        return user_doc.get("warned", None)

    def fetch_last_module(self):
        user_doc = self.find_user_doc()
        if user_doc is None:
            return None
        return user_doc.get("last_module", None)

    def update_last_module(self):
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]},
            {"$set": {"last_module": st.session_state.selected_module}},
        )

    def fetch_corrected_module_topics(self, module):
        page_content = st.session_state.db.content.find_one({"lecture_name": module})
        if page_content and "corrected_lecturepath_topics" in page_content:
            return page_content["corrected_lecturepath_topics"]
        else:
            return None

    def fetch_info(self):
        # Zorg ervoor dat nonce bestaat voordat je iets anders doet
        if st.session_state.nonce is None:
            print("Nonce is None, cannot fetch user info.")
            return

        # Zoek de gebruiker op met de nonce
        user_doc = st.session_state.db.users.find_one({"nonce": st.session_state.nonce})

        # Als de gebruiker is gevonden
        if user_doc is not None:
            st.session_state.username["name"] = user_doc["username"]
            st.session_state.username["role"] = (
                "student"  # TODO: HARDCODED, maar moet dynamisch worden bepaald met de SURF-token
            )
            print("User found with username:", st.session_state.username["name"])

        # Als geen gebruiker is gevonden en de username nog niet is ingesteld
        elif st.session_state.username["name"] is None:
            print("No user found with the nonce.")

        # Als geen `user_doc` is gevonden, maar de username al wel is ingesteld
        else:
            print(
                "No user doc found, but username exists:",
                st.session_state.username["name"],
            )

    def invalidate_nonce(self):
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]}, {"$set": {"nonce": None}}
        )
        st.session_state.nonce = None

    def fetch_all_documents(self):
        collection = st.session_state.db[self.users_collection_name]
        return list(collection.find({}))

    def find_user_doc(self):
        return st.session_state.db.users.find_one(
            {"username": st.session_state.username["name"]}
        )

    def get_progress_counter(self, module, user_doc) -> dict:
        progress_counter = (
            user_doc.get("progress", {})
            .get(module, {})
            .get("learning", {})
            .get("progress_counter", None)
        )
        return progress_counter if progress_counter is not None else {}

    def update_progress_counter_for_segment(self, module, new_progress_count):
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]},
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
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]},
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
        st.session_state.db.users.update_one(
            {"username": st.session_state.username["name"]},
            {"$set": {"last_phase": phase}},
        )

    def update_module_status(self, status):
        """
        Update the status of the module, such as 'not_recorded', 'generated', 'corrected' etc.
        """
        st.session_state.db.content.update_one(
            {"lecture_name": st.session_state.selected_module},
            {"$set": {"status": status}},
        )

    def fetch_module_status(self):
        """
        Fetches if the module has been generated and checked on quality by teacher.
        """
        module = st.session_state.db.content.find_one(
            {"lecture_name": st.session_state.selected_module}
        )

        if module is None:
            return None
        else:
            return module["status"]
