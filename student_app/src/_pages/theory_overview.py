from datetime import timedelta
import streamlit as st
import base64
from models.lecturepath import LecturePath
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess


class TheoryOverview:
    def __init__(self) -> None:
        self.db = db_config.connect_db(st.session_state.use_mongodb)
        self.db_dal = DatabaseAccess()
        self.module_title = self.db_dal.fetch_last_module()[1:]

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
        st.title(f"Theorie Overzicht - {self.module_title}")
        st.write("\n")

    def show_theory_for_topic(self, topic):
        for segment in topic["segments"]:
            content_container = st.container()
            content_cols = content_container.columns([1, 1])
            if segment["segment_type"] == "theory":
                # Create invisible container to cluster each infosegment with the corresponding question segment(s) and image

                with content_cols[0]:
                    title = segment["segment_title"]
                    text = segment["segment_text"]
                    # Write the theory contents
                    st.markdown(
                        f'<p class="size-4">{title}</p>', unsafe_allow_html=True
                    )
                    st.write(text)

                with content_cols[1]:
                    if (image_path := segment["segment_image_path"]) is not None:
                        image_base64 = self.convert_image_base64(image_path)
                        image_html = f"""
                                    <div style='text-align: center; margin: 10px;'>
                                        <img src='data:image/png;base64,{image_base64}' alt='image can't load' style='max-width: 100%; max-height: 500px'>
                                    </div>"""
                        st.markdown(image_html, unsafe_allow_html=True)

            elif segment["segment_type"] == "question":
                with content_cols[0]:
                    question = segment["segment_question"]
                    st.markdown(
                        f'<p class="size-4-question">{question}</p>',
                        unsafe_allow_html=True,
                    )

                    # Render normal or MC answer
                    if (answer := segment["segment_answer"]) is None:
                        mc_answers = segment["segment_answers"]
                        st.write(f"_{mc_answers['correct_answer']}._")
                    else:
                        st.write(f"_{answer}_")

    @st.cache_data(ttl=timedelta(hours=4))
    def get_module_data(_self, module_name_underscored):
        _self.db_dal.get_topics_list_from_db(module_name_underscored)
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

    def run(self):
        """
        Renders the overview page with the lecture title and the topics from the
        lecture in seperate containers that allow the user to look at the contents
        and to select the topics they want to learn.
        """
        self.set_styling()  # for texts
        self.db_dal.update_last_phase("theory-overiew")

        module_name_underscored = st.session_state.selected_module.replace(" ", "_")
        topics_data = self.get_module_data(module_name_underscored)

        self.render_title()

        for topic_index, topic in enumerate(topics_data):
            st.subheader(topic["topic_title"])
            self.show_theory_for_topic(topic)

        # Spacing
        st.write("\n")
