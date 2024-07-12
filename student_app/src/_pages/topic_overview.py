import streamlit as st
import base64
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess
from utils.utils import Utils


class TopicOverview:
    def __init__(self) -> None:
        self.db = db_config.connect_db(st.session_state.use_mongodb)
        self.db_dal = DatabaseAccess()
        self.utils = Utils()
        self.module_name = st.session_state.selected_module.replace(" ", "_")
        self.module_title = " ".join(self.module_name.split("_")[1:])
        self.module_number = self.module_name.split("_")[0]

    def convert_image_base64(self, image_path):
        """
        Converts image in working dir to base64 format so it is
        compatible with html.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    def set_styling(self):
        st.markdown(
            """
            <style>
            .size-4 {
                font-size:20px !important;
                font-weight: bold;
            }
            .size-4-question {
                font-size: 16px !important;
                font-weight: bold;
                font-style: bold;
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render_title(self):
        # container = st.container(border=True)
        # header_cols = container.columns([0.1, 40])

        # with header_cols[1]:
        #     st.title(f"College {self.module_number} — {self.module_title}")
        #     st.write("\n")
        st.title(f"College {self.module_number} — {self.module_title}")

    def start_learning_page(self, topic_index):
        """
        Updates the segment index and calls the function to render the correct page
        corresponding to the selected topic.
        """
        # Determine which segment has to be displayed for the selected topic
        segment_index = self.db_dal.get_index_first_segment_in_topic(topic_index)

        # Change the segment index to the index corresponding to the selected topic
        self.db.users.update_one(
            {"username": st.session_state.username},
            {
                "$set": {
                    f"progress.{st.session_state.selected_module}.learning.segment_index": segment_index
                }
            },
        )
        # Change the 'phase' from overview to learning to render the learning page
        st.session_state.selected_phase = "learning"

    def create_empty_progress_dict(self, module):
        """
        Creates an empty dictionary that contains the JSON
        index of the segment as key and the number of times
        the user answered a question.
        """
        empty_dict = {}

        st.session_state.page_content = self.db_dal.fetch_module_content(module)

        number_of_segments = len(st.session_state.page_content["segments"])

        # Create a dictionary with indexes (strings) as key and None as value
        empty_dict = {str(i): None for i in range(number_of_segments)}

        return empty_dict

    def is_topic_completed(self, topic_index, module):
        """
        Checks if the user made all segments for this topic.
        """
        topic_segment_indexes = self.db_dal.get_topic_segment_indexes(
            module, topic_index
        )
        user_doc = self.db_dal.find_user_doc()
        progress_count = self.db_dal.fetch_progress_counter(module, user_doc)

        # If the progress_count is None, then it needs to be added
        if progress_count is None:
            empty_dict = self.create_empty_progress_dict(module)
            self.db_dal.add_progress_counter(module, empty_dict)
            return False

        for index in topic_segment_indexes:
            if progress_count.get(str(index), None) is None:
                return False

        return True

    def get_module_data(_self, module_name_underscored):
        _self.db_dal.topics_list = _self.db_dal.get_topics_list_from_db(
            module_name_underscored
        )

        topics_data = []

        for topic in _self.db_dal.topics_list:
            topic_data = {
                "topic_title": topic["topic_title"],
                "segment_indexes": topic["segment_indexes"],
                "segments": [],
            }

            _self.db_dal.get_segments_list_from_db(module_name_underscored)
            for segment_index in topic["segment_indexes"]:
                segments_list = _self.db_dal.get_segments_list_from_db(
                    module_name_underscored
                )
                segment_type = _self.db_dal.get_segment_type(segment_index)
                segment_title = (
                    segments_list[segment_index]["title"]
                    if segment_type == "theory"
                    else None
                )
                segment_text = (
                    segments_list[segment_index]["text"]
                    if segment_type == "theory"
                    else None
                )
                segment_question = (
                    segments_list[segment_index].get("question", None)
                    if segment_type == "question"
                    else None
                )
                segment_answers = (
                    segments_list[segment_index].get("answers", None)
                    if segment_type == "question"
                    else None
                )
                segment_answer = (
                    segments_list[segment_index].get("answer", None)
                    if segment_type == "question"
                    else None
                )
                segment_image_file_name = segments_list[segment_index].get(
                    "image", None
                )
                segment_image_path = (
                    _self.db_dal.get_image_path(segment_image_file_name)
                    if segment_image_file_name
                    else None
                )

                segment_data = {
                    "segment_type": segment_type,
                    "segment_title": segment_title,
                    "segment_text": segment_text,
                    "segment_image_path": segment_image_path,
                    "segment_question": segment_question,
                    "segment_answers": segment_answers,
                    "segment_answer": segment_answer,
                }

                topic_data["segments"].append(segment_data)

            topics_data.append(topic_data)

        return topics_data

    def render_topic_containers(self):
        """
        Renders the container that contains the topic title, start button,
        and theory and questions for one topic of the lecture.
        """
        module_name_underscored = st.session_state.selected_module.replace(" ", "_")
        topics_data = self.get_module_data(module_name_underscored)

        for topic_index, topic in enumerate(topics_data):
            container = st.container(border=True)
            cols = container.columns([0.02, 6, 2])

            with cols[1]:
                # Check if user made all segments in topic
                if self.is_topic_completed(topic_index, module_name_underscored):
                    topic_status = "✅"
                else:
                    topic_status = "⬜"

                topic_title = topic["topic_title"]
                st.subheader(f"{topic_index + 1}. {topic_title} {topic_status}")

            with cols[2]:
                # Button that starts the learning phase at the first segment of this topic
                st.button(
                    "Start",
                    key=f"start_{topic_index + 1}",
                    on_click=self.start_learning_page,
                    args=(topic_index,),
                    use_container_width=True,
                )

    def render_page(self):
        """
        Renders the overview page with the lecture title and the topics from the
        lecture in seperate containers that allow the user to look at the contents
        and to select the topics they want to learn.
        """
        self.set_styling()  # for texts
        self.db_dal.update_last_phase("topics")

        self.render_title()
        self.utils.add_spacing(2)

        self.render_topic_containers()  # Module given for
