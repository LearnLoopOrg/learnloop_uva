from utils.utils import Utils
import streamlit as st
from dotenv import load_dotenv
import json
from PIL import Image

load_dotenv()


class QualityCheck:
    def __init__(self):
        self.utils = Utils()

    def run(self):
        self.display_header()
        data_modules, data_modules_topics = self.load_module_data()
        segments, topics = data_modules["segments"], data_modules_topics["topics"]
        self.initialize_session_state(segments, topics)
        self.display_sidebar_page_navigation(topics)
        self.display_segments(segments, topics)
        self.display_save_button()

    def display_sidebar_page_navigation(self, topics):
        # Render the sidebar with links to the topics
        with st.sidebar:
            topic_titles = [topic["topic_title"] for topic in topics]
            # Define CSS styles
            css_styles = """
            <style>
            </style>
            """

            # Render CSS styles
            st.markdown(css_styles, unsafe_allow_html=True)

            # Render navigation with heading
            col = st.columns(1)
            with col[0]:
                st.markdown("<h2>Index</h2>", unsafe_allow_html=True)
                for i, topic_title in enumerate(topic_titles):
                    st.html(f"""<div style="display: inline-block; color: white; padding: 10px 0px; margin:0px; gap: 0rem; text-align: left; text-decoration: none; border-radius: 5px; transition: background-color 0.3s;">
            <a href="#{topic_title}" style="color: black; text-decoration: none;">{i + 1} - {topic_title}</a>
        </div>""")
                st.html("</div>")

    def display_header(self):
        lecture_number, lecture_name = st.session_state.selected_module.split(" ", 1)
        st.title(f"Kwaliteitscheck {lecture_name}: college {lecture_number}")
        st.write(
            "Controleer de onderstaande gegenereerde oefenmaterialen om er zeker van te zijn dat studenten het juiste leren. "
            "Pas de afbeelding, theorie, vraag of het antwoord aan, of verwijder deze indien nodig. "
            "Als je klaar bent, kun je de oefenmaterialen direct delen met studenten door op de button onderaan te drukken."
        )

    def load_module_data(self):
        module_name = st.session_state.selected_module.replace(" ", "_")
        data_modules = self.utils.download_content_from_blob_storage(
            "content", f"modules/{module_name}.json"
        )
        data_modules = json.loads(data_modules)
        data_modules_topics = self.utils.download_content_from_blob_storage(
            "content", f"topics/{module_name}.json"
        )
        data_modules_topics = json.loads(data_modules_topics)
        return data_modules, data_modules_topics

    def initialize_session_state(self, segments, topics):
        for segment_id, segment in enumerate(segments):
            segment_id = str(segment_id)
            if f"button_state{segment_id}" not in st.session_state:
                st.session_state[f"button_state{segment_id}"] = "no"
            self.initialize_segment_state(segment_id, segment)

    def initialize_segment_state(self, segment_id, segment):
        segment_type = segment["type"]
        if segment_type == "theory":
            self.initialize_theory_state(segment_id, segment)
        elif segment_type == "question":
            self.initialize_question_state(segment_id, segment)

    def initialize_theory_state(self, segment_id, segment):
        if segment_id not in st.session_state:
            st.session_state[segment_id] = segment["text"]
        if f"new-{segment_id}" not in st.session_state:
            st.session_state[f"new-{segment_id}"] = ""

    def initialize_question_state(self, segment_id, segment):
        if segment_id not in st.session_state:
            st.session_state[segment_id] = segment["question"]
        if f"new-{segment_id}" not in st.session_state:
            st.session_state[f"new-{segment_id}"] = ""
        if "answers" in segment:
            self.initialize_answer_state(segment_id, segment["answers"])
        elif "answer" in segment:
            self.initialize_single_answer_state(segment_id, segment)

    def initialize_answer_state(self, segment_id, answers):
        if f"{segment_id}-answers-correct_answer" not in st.session_state:
            st.session_state[f"{segment_id}-answers-correct_answer"] = answers[
                "correct_answer"
            ]
        if f"{segment_id}-answers-wrong_answers" not in st.session_state:
            wrong_answers_enumeration = self.utils.list_to_enumeration(
                answers["wrong_answers"]
            )
            st.session_state[f"{segment_id}-answers-wrong_answers"] = (
                wrong_answers_enumeration
            )
        if f"new-{segment_id}-answers-correct_answer" not in st.session_state:
            st.session_state[f"new-{segment_id}-answers-correct_answer"] = ""
        if f"new-{segment_id}-answers-wrong_answers" not in st.session_state:
            st.session_state[f"new-{segment_id}-answers-wrong_answers"] = ""

    def initialize_single_answer_state(self, segment_id, segment):
        if f"{segment_id}-answer" not in st.session_state:
            st.session_state[f"{segment_id}-answer"] = segment["answer"]
        if f"new-{segment_id}-answer" not in st.session_state:
            st.session_state[f"new-{segment_id}-answer"] = ""

    def display_segments(self, segments, topics):
        topic_id, topic_segment_id = 0, 0
        for segment_id, segment in enumerate(segments):
            segment_id_str = str(segment_id)
            if topic_segment_id == 0:
                st.subheader(
                    f"Onderwerp {topic_id + 1} / {len(topics)} - {topics[topic_id]["topic_title"]}",
                    anchor=topics[topic_id]["topic_title"],
                )
            self.display_segment(segment_id_str, segment)
            topic_id, topic_segment_id = self.update_topic_indices(
                topic_id, topic_segment_id, topics
            )

    def display_segment(self, segment_id, segment):
        with st.container(border=True):
            if segment.get("image"):
                self.display_image(segment["image"])
            self.display_segment_content(segment_id, segment)
            self.display_toggle_button(segment_id)

    def resize_image_to_max_height(self, image: Image.Image, max_height):
        # Calculate the new width maintaining the aspect ratio
        aspect_ratio = image.width / image.height
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

        # Resize the image
        resized_img = image.resize((new_width, new_height))

        return resized_img

    def display_image(self, image_path):
        image = self.utils.download_image_from_blob_storage("images", image_path)
        resized_image = self.resize_image_to_max_height(image, 300)

        st.image(resized_image, use_column_width="auto")

    def display_segment_content(self, segment_id, segment):
        segment_type = segment["type"]
        if segment_type == "theory":
            self.display_theory_segment(segment_id, segment)
        elif segment_type == "question":
            self.display_question_segment(segment_id, segment)

    def display_theory_segment(self, segment_id, segment):
        st.markdown(f"**Theorie: {segment['title']}**")
        st.text_area(
            "Theorie",
            key=segment_id,
            on_change=self.utils.save_st_change(f"new-{segment_id}", segment_id),
            label_visibility="collapsed",
        )

    def display_question_segment(self, segment_id, segment):
        st.markdown("**Vraag:**")
        st.text_area(
            "Vraag",
            key=segment_id,
            on_change=self.utils.save_st_change(f"new-{segment_id}", segment_id),
            label_visibility="collapsed",
        )
        if "answers" in segment:
            self.display_answer_segment(segment_id, segment["answers"])
        elif "answer" in segment:
            self.display_single_answer_segment(segment_id, segment["answer"])

    def display_answer_segment(self, segment_id, answers):
        st.markdown("*Correct antwoord:*")
        st.text_area(
            "Correct antwoord:",
            key=f"{segment_id}-answers-correct_answer",
            on_change=self.utils.save_st_change(
                f"new-{segment_id}-answers-correct_answer",
                f"{segment_id}-answers-correct_answer",
            ),
            label_visibility="collapsed",
        )
        st.markdown("*Onjuiste antwoorden:*")
        st.text_area(
            "Onjuiste antwoorden:",
            key=f"{segment_id}-answers-wrong_answers",
            on_change=self.utils.save_st_change(
                f"new-{segment_id}-answers-wrong_answers",
                f"{segment_id}-answers-wrong_answers",
            ),
            label_visibility="collapsed",
        )

    def display_single_answer_segment(self, segment_id, answer):
        st.markdown("*Antwoord:*")
        st.text_area(
            "Antwoord:",
            key=f"{segment_id}-answer",
            on_change=self.utils.save_st_change(
                f"new-{segment_id}-answer", f"{segment_id}-answer"
            ),
            label_visibility="collapsed",
        )

    def display_toggle_button(self, segment_id):
        col1, col2 = st.columns([0.9, 0.1])
        with col2:
            button_icon = (
                "❌" if st.session_state[f"button_state{segment_id}"] == "no" else "➕"
            )
            button_help = (
                "Verwijderen"
                if st.session_state[f"button_state{segment_id}"] == "no"
                else "Toevoegen"
            )
            if st.button(
                label=button_icon, key=f"toggle_button{segment_id}", help=button_help
            ):
                self.utils.toggle_button(segment_id)
                st.rerun()

    def update_topic_indices(self, topic_id, topic_segment_id, topics):
        if topic_segment_id == len(topics[topic_id]["segment_indexes"]) - 1:
            topic_id += 1
            topic_segment_id = 0
        else:
            topic_segment_id += 1
        return topic_id, topic_segment_id

    def display_save_button(self):
        if st.button("Opslaan", use_container_width=True):
            segments_list = self.utils.preprocessed_segments(
                st.session_state.selected_module.replace(" ", "_")
            )
            self.utils.upload_modules_json(
                st.session_state.selected_module.replace(" ", "_"), segments_list
            )
            self.utils.upload_modules_topics_json(
                st.session_state.selected_module.replace(" ", "_"), segments_list
            )


if __name__ == "__main__":
    qc = QualityCheck()
    qc.run()
