from datetime import timedelta
from matplotlib import pyplot as plt
import numpy as np
import streamlit as st
import base64
import json
from data.data_access_layer import DatabaseAccess
from utils.openai_client import openai_call, read_prompt
from streamlit_extras.add_vertical_space import add_vertical_space


class LectureInsights:
    def __init__(self) -> None:
        self.db = st.session_state.db
        self.db_dal = DatabaseAccess()
        self.module = ""

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

    def display_header(self):
        cols = st.columns([10, 7, 5])
        with cols[0]:
            st.title(st.session_state.selected_module)

        with cols[1]:
            st.write("\n\n")
            st.subheader("Inzichten")
            st.write(
                "Bekijk de knelpunten van je studenten en focus hierop tijdens je volgende contactmoment."
            )

        st.write("---")

    def start_learning_page(self, topic_index):
        """
        Updates the segment index and calls the function to render the correct page
        corresponding to the selected topic.
        """
        # Determine which segment has to be displayed for the selected topic
        segment_index = self.db_dal.get_index_first_segment_in_topic(topic_index)

        # Change the segment index to the index corresponding to the selected topic
        self.db.users.update_one(
            {"username": st.session_state.user_doc["name"]},
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

        st.session_state.page_content = self.db_dal.fetch_corrected_module_content(
            module
        )

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
                _self.db_dal.get_segments_list_from_db(module_name_underscored)
                segment_type = _self.db_dal.get_segment_type(segment_index)
                segment_title = (
                    _self.db_dal.get_segment_title(segment_index)
                    if segment_type == "theory"
                    else None
                )
                segment_text = (
                    _self.db_dal.get_segment_text(segment_index)
                    if segment_type == "theory"
                    else None
                )
                segment_question = (
                    _self.db_dal.get_segment_question(segment_index)
                    if segment_type == "question"
                    else None
                )
                segment_answers = (
                    _self.db_dal.get_segment_mc_answers(segment_index)
                    if segment_type == "question"
                    else None
                )
                segment_answer = (
                    _self.db_dal.get_segment_answer(segment_index)
                    if segment_type == "question"
                    else None
                )
                segment_image_file_name = _self.db_dal.get_segment_image_file_name(
                    segment_index
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
        module_name_underscored = st.session_state.selected_module
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

            with container.expander("Analyse"):
                for segment in topic["segments"]:
                    if segment["segment_type"] == "theory":
                        # Create invisible container to cluster each infosegment with the corresponding question segment(s) and image
                        content_container = st.container()
                        content_cols = content_container.columns([1, 1])

                        with content_cols[0]:
                            title = segment["segment_title"]
                            text = segment["segment_text"]
                            # Write the theory contents
                            st.markdown(
                                f'<p class="size-4">{title}</p>', unsafe_allow_html=True
                            )
                            st.write(text)

                        with content_cols[1]:
                            if (
                                image_path := segment["segment_image_path"]
                            ) is not None:
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

    def get_open_question_stats(self, module, question_index, results):
        question_stats = {}
        question_stats["scores"] = []
        question_stats["feedback_per_student"] = []
        question_stats["student_answers"] = []

        for result in results:
            for question in result["progress"][module]["feedback"]["questions"]:
                if not question.get("segment_index") == question_index:
                    continue

                question_stats["scores"].append(question.get("score"))
                question_stats["feedback_per_student"].append(question.get("feedback"))
                question_stats["student_answers"].append(question.get("student_answer"))

        return question_stats

    def get_mc_question_stats(self, module, question_index, results):
        question_stats = {}
        question_stats["scores"] = []
        question_stats["student_answers"] = []

        for result in results:
            for question in result["progress"][module]["feedback"]["questions"]:
                if not question.get("segment_index") == question_index:
                    continue

                question_stats["scores"].append(question.get("score"))
                question_stats["student_answers"].append(question.get("student_answer"))

        return question_stats

    # @st.cache_data(ttl=timedelta(hours=4), show_spinner=False)
    def get_question_stats(_self, module, question_index, question_content):
        mongo_module = module
        results = _self.db_dal.fetch_question(mongo_module, question_index)

        if "answers" in question_content:
            return _self.get_mc_question_stats(mongo_module, question_index, results)
        elif "answer" in question_content:
            return _self.get_open_question_stats(mongo_module, question_index, results)
        else:
            raise ValueError("Invalid question type")

    # @st.cache_data(ttl=timedelta(hours=4), show_spinner=False)
    def get_topic_questions_stats(_self, module, questions_content):
        questions_stats = {}
        for question_index, question_content in questions_content.items():
            question_stats = _self.get_question_stats(
                module, question_index, question_content
            )
            questions_stats[question_index] = question_stats
        return questions_stats

    def format_for_analyse_prompt(self, questions_content, questions_stats):
        input_prompt = {}
        for question_index, question_content in questions_content.items():
            input_prompt[question_index] = {}
            input_prompt[question_index]["sub_type"] = (
                "multiple_choice_question"
                if "answers" in question_content
                else "open_question"
            )
            if "answer" in question_content:
                input_prompt[question_index]["feedback_per_student"] = questions_stats[
                    question_index
                ]["feedback_per_student"]
            elif "answers" in question_content:
                input_prompt[question_index]["student_answers"] = questions_stats[
                    question_index
                ]["student_answers"]
                input_prompt[question_index]["correct_answer"] = question_content[
                    "answers"
                ]["correct_answer"]

        return input_prompt

    @st.cache_data(ttl=timedelta(hours=4))
    def analyse_feedback(_self, questions_content, questions_stats):
        input_dict = _self.format_for_analyse_prompt(questions_content, questions_stats)
        input_json = json.dumps(input_dict)

        system_message = read_prompt("analyse_feedback")

        response = openai_call(
            st.session_state.openai_client,
            system_message,
            input_json,
            True,
            max_tokens=4096,
            model=st.session_state.openai_model,
        )
        return response

    def plot_scores(self, scores):
        int_scores = [
            int(float(score.split("/")[0]) / float(score.split("/")[1]))
            for score in scores
        ]

        # Function to categorize scores
        def categorize_scores(scores):
            categories = {
                "Niet gemaakt": 0,
                "Onvoldoende": 0,
                "Voldoende": 0,
                "Goed": 0,
            }
            for score in scores:
                if score < 0.5:
                    categories["Onvoldoende"] += 1
                elif 0.5 <= score < 0.7:
                    categories["Voldoende"] += 1
                elif score >= 0.7:
                    categories["Goed"] += 1
            return categories

        # Categorize the scores
        categories = categorize_scores(int_scores)
        category_names = ["Niet gemaakt", "Onvoldoende", "Voldoende", "Goed"]
        data = np.array(
            [
                categories["Niet gemaakt"],
                categories["Onvoldoende"],
                categories["Voldoende"],
                categories["Goed"],
            ]
        ).reshape(1, -1)
        results = {"Scores": data[0].tolist()}

        # Function to create the horizontal_bar_plot plot
        def horizontal_bar_plot(results, category_names):
            labels = list(results.keys())
            data = np.array(list(results.values()))
            data_cum = data.cumsum(axis=1)
            category_colors = ["white", (0.98, 0.2, 0), "yellow", "lightgreen"]

            fig, ax = plt.subplots(figsize=(10, 1))
            ax.invert_yaxis()
            # ax.xaxis.set_visible(False)
            ax.set_xlim(0, np.sum(data, axis=1).max())
            ax.set_xticks([np.sum(data, axis=1).max()])
            ax.set_xticklabels([np.sum(data, axis=1).max()])

            for i, (colname, color) in enumerate(zip(category_names, category_colors)):
                widths = data[:, i]
                starts = data_cum[:, i] - widths
                ax.barh(
                    labels, widths, left=starts, height=10, label=colname, color=color
                )
                ax.set_yticklabels([])  # Remove y-axis labels

                ax.spines["top"].set_visible(False)  # Remove top border
                ax.spines["right"].set_visible(False)  # Remove right border
                ax.spines["bottom"].set_visible(False)  # Remove bottom border
                ax.spines["left"].set_visible(False)  # Remove left border

                # r, g, b, _ = color
                # text_color = 'white' if r * g * b < 0.5 else 'darkgrey'
                # ax.bar_label(rects, label_type='center', color=text_color)
            # ax.legend(ncols=len(category_names), bbox_to_anchor=(0, 1),
            #         loc='lower left', fontsize='small')

            return fig, ax

        # Create the horizontal_bar_plot plot
        fig, ax = horizontal_bar_plot(results, category_names)

        # Display the plot in Streamlit
        st.pyplot(fig, use_container_width=True)
        pass

    def display_sidebar_page_navigation(self, module, topics):
        # Render the sidebar with links to the topics
        with st.sidebar:
            # Define CSS styles
            css_styles = """
            <style>
            </style>
            """

            # Render CSS styles
            st.markdown(css_styles, unsafe_allow_html=True)

            # Render navigation with heading
            st.html(
                """<div style="display: flex; justify-content: flex-start; gap: 0rem;">"""
            )

            st.markdown(
                """
    <style>
    [data-testid=column]:nth-of-type(1) [data-testid=stVerticalBlock]{
        gap: 0rem;
    }
    </style>
    """,
                unsafe_allow_html=True,
            )

            col1 = st.columns(1)
            with col1[0]:
                st.subheader("Navigatie")
                for i, topic in enumerate(topics):
                    questions_content = self.db_dal.get_topic_questions(
                        module, topic["segment_indexes"]
                    )
                    questions_stats = self.get_topic_questions_stats(
                        module, questions_content
                    )

                    all_scores = []
                    total_achieved_score = 0
                    total_score = 0
                    for _, stats_for_question in questions_stats.items():
                        for score in stats_for_question["scores"]:
                            total_achieved_score += float(score.split("/")[0])
                            total_score += float(score.split("/")[1])
                        all_scores.extend(
                            stats_for_question["scores"]
                        )  # Assuming 'scores' is always present
                    percentage_correct_topic = (
                        total_achieved_score / total_score if total_score > 0 else -1
                    )
                    # i want a red, orange or green color based on the percentage correct

                    st.html(f"""<div style="display: inline-block; color: white; padding: 10px 0px; margin:0px; gap: 0rem; text-align: left; text-decoration: none; border-radius: 5px; transition: background-color 0.3s;">
            <a href="#{topic["topic_title"]}" style="color: black; text-decoration: none;">{self._get_icon_based_on_percentage(percentage_correct_topic)} {i + 1} - {topic["topic_title"]}</a>
        </div>""")
                    st.html("</div>")

    def get_correct_answer(self, question):
        if "answers" in question:
            return question["answers"]["correct_answer"]
        if "answer" in question:
            return question["answer"]

    def _get_icon_based_on_percentage(self, percentage: float) -> str:
        """
        Returns an icon based on the given percentage.

        Args:
            percentage (float): The percentage value.

        Returns:
            str: The icon corresponding to the percentage. If the percentage is less than 0, the icon is a white circle.

        """
        if percentage < 0:
            icon = "⚪️"
        elif percentage < 0.5:
            icon = "🔴"
        elif percentage < 0.8:
            icon = "🟠"
        else:
            icon = "🟢"
        return icon

    def show_topic_feedback(self, module, topic, topic_index):
        questions_content = self.db_dal.get_topic_questions(
            module, topic["segment_indexes"]
        )
        questions_stats = self.get_topic_questions_stats(module, questions_content)

        all_scores = []
        total_achieved_score = 0
        total_score = 0
        for question_index, stats_for_question in questions_stats.items():
            for score in stats_for_question["scores"]:
                total_achieved_score += float(score.split("/")[0])
                total_score += float(score.split("/")[1])
            all_scores.extend(
                stats_for_question["scores"]
            )  # Assuming 'scores' is always present

        with st.container():
            percentage_correct_topic = (
                total_achieved_score / total_score if total_score > 0 else -1
            )
            icon = self._get_icon_based_on_percentage(percentage_correct_topic)
            st.subheader(
                f"{icon} {topic['topic_title']}",
                anchor=topic["topic_title"],
            )
            if total_score == 0:
                st.markdown(
                    '<span style="color: gray;">Nog geen studenten hebben deze vragen gemaakt.</span>',
                    unsafe_allow_html=True,
                )
                return

            # st.markdown(
            #     f'<span style="color: gray;">👥 Studenten: {len(all_scores)}</span>',
            #     unsafe_allow_html=True,
            # )
            st.markdown(
                f'<span style="color: gray;">📊 Gemiddelde: {percentage_correct_topic * 100:.0f}% correct</span>',
                unsafe_allow_html=True,
            )
            with st.expander(
                "Analyse per vraag", expanded=True if topic_index == 0 else False
            ):
                feedback_analyses = self.analyse_feedback(
                    questions_content, questions_stats
                )
                for j, (question_index, question_content) in enumerate(
                    questions_content.items()
                ):
                    question_stats = questions_stats[question_index]
                    scores_for_question = question_stats["scores"]
                    max_score = 0
                    for score in scores_for_question:
                        total_achieved_score += float(score.split("/")[0])
                        max_score = float(score.split("/")[1])
                        total_score += max_score

                    percentage_correct_question = total_achieved_score / total_score
                    # i want a red, orange or green color based on the percentage correct

                    if len(questions_stats) > 0:
                        st.markdown(
                            f'<span style="font-size: 1.2em;">{self._get_icon_based_on_percentage(percentage_correct_question)} **{question_content["question"].encode("utf-8").decode("unicode_escape")}**</span>',
                            unsafe_allow_html=True,
                        )

                    else:
                        st.markdown(f"**{question_content['question']}**")
                    if (
                        feedback_analyses is not None
                        and "title" in feedback_analyses[str(question_index)]
                    ):
                        st.html(f"""
        <div style="border-radius: 0.5rem; padding: 1rem;padding-bottom:0.1rem; background-color: #FFFCED;">
            <strong>{feedback_analyses[str(question_index)]["title"]}</strong>
            <p>{feedback_analyses[str(question_index)]["text"]}</p>
        </div>""")
                    else:
                        st.error("Feedback analyse kon niet worden geladen")

                    columns = st.columns([5, 2])

                    with columns[0]:
                        st.markdown(
                            '<span style="color: gray; padding-left: 1rem;">**Antwoordmodel**</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<p style="color: gray; padding-left: 1rem">{self.get_correct_answer(question_content)}</p>',
                            unsafe_allow_html=True,
                        )

                    with columns[1]:
                        st.markdown(
                            '<span style="color: gray;">**Statistieken**</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<span style="color: gray;">👥 Studenten: {len(scores_for_question)}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<span style="color: gray;">📊 Gemiddelde: {((total_achieved_score/total_score) * max_score):.1f}/{max_score} punten</span>',
                            unsafe_allow_html=True,
                        )
                    if j < len(questions_content) - 1:
                        add_vertical_space(2)
                    j += 1

    def run(self):
        """
        Renders the overview page with the lecture title and the topics from the
        lecture in seperate containers that allow the user to look at the contents
        and to select the topics they want to learn.
        """
        # Fetch module info to be rendered
        self.module = st.session_state.selected_module
        self.db_dal = st.session_state.db_dal
        st.session_state.page_content = self.db_dal.fetch_original_module_content(
            self.module
        )

        self.set_styling()
        self.display_header()

        st.write("\n")
        topics = self.db_dal.get_topics_list_from_db(self.module)
        for topic_index, topic in enumerate(topics):
            self.show_topic_feedback(self.module, topic, topic_index)

        self.display_sidebar_page_navigation(self.module, topics)
