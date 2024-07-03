from matplotlib import pyplot as plt
import numpy as np
import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import json
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess, ContentAccess
from utils.openai_client import openai_call, read_prompt
from utils.constants import QuestionType

import pandas as pd
import altair as alt


class LectureInsights:
    def __init__(self) -> None:
        self.db = db_config.connect_db(st.session_state.use_mongodb)
        self.db_dal = DatabaseAccess()
        self.cont_dal = ContentAccess()
        self.module_title = st.session_state.selected_module
        
    def convert_image_base64(self, image_path):
        """
        Converts image in working dir to base64 format so it is 
        compatible with html.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
        
    
    def set_styling(self):
        st.markdown("""
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
            """, unsafe_allow_html=True)

        
    def render_title(self):
        container = st.container(border=True)
        header_cols = container.columns([0.1, 40])

        with header_cols[1]:
            st.title(self.module_title)
            st.write("\n")


    def start_learning_page(self, topic_index):
        """
        Updates the segment index and calls the function to render the correct page
        corresponding to the selected topic.
        """
        # Determine which segment has to be displayed for the selected topic
        segment_index = self.cont_dal.get_index_first_segment_in_topic(topic_index)

        # Change the segment index to the index corresponding to the selected topic
        self.db.users.update_one(
            {"username": st.session_state.username},
            {"$set": {f"progress.{st.session_state.selected_module}.learning.segment_index": segment_index}}
        )
        # Change the 'phase' from overview to learning to render the learning page
        st.session_state.selected_phase = 'learning'
    
    def create_empty_progress_dict(self, module):
        """
        Creates an empty dictionary that contains the JSON
        index of the segment as key and the number of times  
        the user answered a question.
        """
        empty_dict = {}

        st.session_state.page_content = self.cont_dal.fetch_module_content(module)

        number_of_segments = len(st.session_state.page_content['segments'])
        
        # Create a dictionary with indexes (strings) as key and None as value
        empty_dict = {str(i): None for i in range(number_of_segments)}
        
        return empty_dict
    
    def is_topic_completed(self, topic_index, module):
        """
        Checks if the user made all segments for this topic.
        """
        topic_segment_indexes = self.cont_dal.get_topic_segment_indexes(module, topic_index)
        user_doc = self.db_dal.find_user_doc()
        progress_count = self.db_dal.fetch_progress_counter(module, user_doc)
        
        # If the progress_count is None, then it needs to be added
        if progress_count is None:
            empty_dict = self.create_empty_progress_dict(module)
            self.db_dal.add_progress_counter(module, empty_dict)
            return False
        
        for index in topic_segment_indexes:
            if progress_count.get(str(index), None) == None:
                return False
        
        return True
    
    
    def get_module_data(_self, module_name_underscored):
        _self.cont_dal.get_topics_list(module_name_underscored)
        topics_data = []

        for topic in _self.cont_dal.topics_list:
            topic_data = {
                'topic_title': topic['topic_title'],
                'segment_indexes': topic['segment_indexes'],
                'segments': []
            }

            _self.cont_dal.get_segments_list(module_name_underscored)
            for segment_index in topic['segment_indexes']:
                _self.cont_dal.get_segments_list(module_name_underscored)
                segment_type = _self.cont_dal.get_segment_type(segment_index)
                segment_title = _self.cont_dal.get_segment_title(segment_index) if segment_type == "theory" else None
                segment_text = _self.cont_dal.get_segment_text(segment_index) if segment_type == "theory" else None
                segment_question = _self.cont_dal.get_segment_question(segment_index) if segment_type == "question" else None
                segment_answers = _self.cont_dal.get_segment_mc_answers(segment_index) if segment_type == "question" else None
                segment_answer = _self.cont_dal.get_segment_answer(segment_index) if segment_type == "question" else None
                segment_image_file_name = _self.cont_dal.get_segment_image_file_name(segment_index)
                segment_image_path = _self.cont_dal.get_image_path(segment_image_file_name) if segment_image_file_name else None

                segment_data = {
                    'segment_type': segment_type,
                    'segment_title': segment_title,
                    'segment_text': segment_text,
                    'segment_image_path': segment_image_path,
                    'segment_question': segment_question,
                    'segment_answers': segment_answers,
                    'segment_answer': segment_answer,
                }

                topic_data['segments'].append(segment_data)

            topics_data.append(topic_data)

        return topics_data


    def render_topic_containers(self):
        """
        Renders the container that contains the topic title, start button,
        and theory and questions for one topic of the lecture.
        """
        module_name_underscored = st.session_state.selected_module.replace(' ', '_')
        topics_data = self.get_module_data(module_name_underscored)

        for topic_index, topic in enumerate(topics_data):
            container = st.container(border=True)
            cols = container.columns([0.02, 6, 2])

            with cols[1]:
                # Check if user made all segments in topic
                if self.is_topic_completed(topic_index, module_name_underscored):
                    topic_status = '✅'
                else:
                    topic_status = '⬜'
                
                topic_title = topic['topic_title']
                st.subheader(f"{topic_index + 1}. {topic_title} {topic_status}")

            with cols[2]:
                # Button that starts the learning phase at the first segment of this topic
                st.button("Start", key=f"start_{topic_index + 1}", on_click=self.start_learning_page, args=(topic_index,), use_container_width=True)

            with container.expander("Analyse"):
                for segment in topic['segments']:
                    if segment['segment_type'] == "theory":
                        # Create invisible container to cluster each infosegment with the corresponding question segment(s) and image
                        content_container = st.container()
                        content_cols = content_container.columns([1, 1])

                        with content_cols[0]:
                            title = segment['segment_title']
                            text = segment['segment_text']
                            # Write the theory contents
                            st.markdown(f'<p class="size-4">{title}</p>', unsafe_allow_html=True)
                            st.write(text)

                        with content_cols[1]:
                            if (image_path := segment['segment_image_path']) is not None:
                                image_base64 = self.convert_image_base64(image_path)
                                image_html = f"""
                                    <div style='text-align: center; margin: 10px;'>
                                        <img src='data:image/png;base64,{image_base64}' alt='image can't load' style='max-width: 100%; max-height: 500px'>
                                    </div>"""
                                st.markdown(image_html, unsafe_allow_html=True)

                    elif segment['segment_type'] == "question":
                        with content_cols[0]:
                            question = segment['segment_question']
                            st.markdown(f'<p class="size-4-question">{question}</p>', unsafe_allow_html=True)
                            
                            # Render normal or MC answer
                            if (answer := segment['segment_answer']) is None:
                                mc_answers = segment['segment_answers']
                                st.write(f"_{mc_answers['correct_answer']}._")
                            else:
                                st.write(f"_{answer}_")
                                
    
    def get_open_question_stats(self, module, question_index, results):
        question_stats = {}
        question_stats["scores"] = []
        question_stats["feedback_per_student"] = []
        question_stats["student_answers"] = []
        
        for result in results:
            for question in result['progress'][module]['feedback']['questions']:
                if not question.get('segment_index') == question_index:
                    continue
                
                question_stats["scores"].append(question.get("score")) 
                question_stats["feedback_per_student"].append(question.get('feedback'))
                question_stats["student_answers"].append(question.get('student_answer'))
        
        return question_stats
    
    def get_mc_question_stats(self, module, question_index, results):
        question_stats = {}
        question_stats["scores"] = []
        question_stats["student_answers"] = []
        
        for result in results:
            for question in result['progress'][module]['feedback']['questions']:
                if not question.get('segment_index') == question_index:
                    continue
                
                question_stats["scores"].append(question.get("score")) 
                question_stats["student_answers"].append(question.get('student_answer'))
        
        return question_stats
        
                                
    def get_question_stats(self, module, question_index, question_content):
        mongo_module = module.replace("_", " ")
        results = self.db_dal.fetch_question(mongo_module, question_index)
        
        if question_content["sub_type"] == QuestionType.MULTIPLE_CHOICE_QUESTION.value:
            return self.get_mc_question_stats(mongo_module, question_index, results)
        
        if question_content["sub_type"] == QuestionType.OPEN_QUESTION.value:
            return self.get_open_question_stats(mongo_module, question_index, results)
    
    def get_topic_questions_stats(self, module, questions_content):

        questions_stats = {}
        for question_index, question_content in questions_content.items():
            question_stats = self.get_question_stats(module, question_index, question_content)
            questions_stats[question_index] = question_stats
        return questions_stats
    
    def format_for_analyse_prompt(self, questions_content, questions_stats):
        #Input format prompt
            #{2: {sub_type: "open_question", "feedback_per_student": ["Feedback student 1", "Feedback student 2"]},
            #{4: {sub_type: "multiple_choice_question", correct_answer: "", "student_answers": ["", ""]}}
        # }
        input_prompt = {}
        for question_index, question_content in questions_content.items():
            input_prompt[question_index] = {}
            input_prompt[question_index]["sub_type"] = question_content["sub_type"]
            if question_content["sub_type"] == QuestionType.OPEN_QUESTION.value:
                input_prompt[question_index]["feedback_per_student"] = questions_stats[question_index]["feedback_per_student"]
            elif question_content["sub_type"] == QuestionType.MULTIPLE_CHOICE_QUESTION.value:
                input_prompt[question_index]["student_answers"] = questions_stats[question_index]["student_answers"]
                input_prompt[question_index]["correct_answer"] = question_content["answers"]["correct_answer"]
        
        return input_prompt
    
    def analyse_feedback(self, questions_content, questions_stats):
        input_dict = self.format_for_analyse_prompt(questions_content, questions_stats)
        input_json = json.dumps(input_dict)
        
        system_message = read_prompt("analyse_feedback")
        
        response = openai_call(st.session_state.openai_client, system_message, input_json, True)
        return response
    
    # def insert_segment_indexes_in_feedback(self):
    #     users = self.db.users.find()
    #     for user in users:
    #         if not "progress" in user:
    #             continue
    #         adapted = False
    #         for module in user["progress"]:
    #             for module in user["progress"]:
    #                 if "feedback" in user["progress"][module]:
    #                     for question in user["progress"][module]["feedback"]["questions"]:
    #                         segment_index = self.cont_dal.find_segment_index(question["question"], module)
    #                         question["segment_index"] = segment_index
    #                         adapted = True
    #     # print(2)
    #         if adapted:
    #             self.db.users.update_one({'_id': user['_id']}, {'$set': user})
        #loop trough users
            #loop trough modules
                #loop trough questions
                    #segment_index = find_segment_index(question.text, module)
                    #update this question with segment_index
                    
                    
            
        
        pass
    

    def plot_scores(self, scores):
        int_scores = [int(float(score.split('/')[0])/float(score.split('/')[1])) for score in scores]
        
        # Function to categorize scores
        def categorize_scores(scores):
            categories = {
                'Niet gemaakt': 0,
                'Onvoldoende': 0,
                'Voldoende': 0,
                'Goed': 0
            }
            for score in scores:
                if score < 0.5:
                    categories['Onvoldoende'] += 1
                elif 0.5 <= score < 0.7:
                    categories['Voldoende'] += 1
                elif score >= 0.7:
                    categories['Goed'] += 1
            return categories

        # Categorize the scores
        categories = categorize_scores(int_scores)
        total_scores = sum(categories.values())
        category_names = ['Niet gemaakt', 'Onvoldoende', 'Voldoende', 'Goed']
        data = np.array([categories['Niet gemaakt'], categories['Onvoldoende'], categories['Voldoende'], categories['Goed']]).reshape(1, -1)
        results = {'Scores': data[0].tolist()}

        # Function to create the horizontal_bar_plot plot
        def horizontal_bar_plot(results, category_names):
            labels = list(results.keys())
            data = np.array(list(results.values()))
            data_cum = data.cumsum(axis=1)
            category_colors = ['white', (0.98, 0.2, 0), 'yellow', 'lightgreen']

            
            fig, ax = plt.subplots(figsize=(10, 1))
            ax.invert_yaxis()
            # ax.xaxis.set_visible(False)
            ax.set_xlim(0, np.sum(data, axis=1).max())
            ax.set_xticks([np.sum(data, axis=1).max()])
            ax.set_xticklabels([np.sum(data, axis=1).max()])
            
            
            for i, (colname, color) in enumerate(zip(category_names, category_colors)):
                widths = data[:, i]
                starts = data_cum[:, i] - widths 
                rects = ax.barh(labels, widths, left=starts, height=10,
                                label=colname, color=color)
                ax.set_yticklabels([])  # Remove y-axis labels
                
                ax.spines['top'].set_visible(False)  # Remove top border
                ax.spines['right'].set_visible(False)  # Remove right border
                ax.spines['bottom'].set_visible(False)  # Remove bottom border
                ax.spines['left'].set_visible(False)  # Remove left border
                
                
                
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
    
    def get_correct_answer(self, question):
        if question["sub_type"] == QuestionType.MULTIPLE_CHOICE_QUESTION.value:
            return question["answers"]["correct_answer"]
        if question["sub_type"] == QuestionType.OPEN_QUESTION.value:
            return question["answer"]
            
    def show_topic_feedback(self, module, topic):
        questions_content = self.cont_dal.get_topic_questions(module, topic["segment_indexes"])
        questions_stats = self.get_topic_questions_stats(module, questions_content)

        
        feedback_analyses = self.analyse_feedback(questions_content, questions_stats)
        
        with st.container():
            col1,col2 = st.columns(2)
            with col1:
                st.title(topic["topic_title"])
            with col2:
                all_scores = []
                for question_index, stats in questions_stats.items():
                    all_scores.extend(stats['scores'])  # Assuming 'scores' is always present
                self.plot_scores(all_scores)

            st.write(feedback_analyses['analysis'])
            with st.expander("Analyse per vraag"):
                for question_index, question_content in questions_content.items():
                    question_stats = questions_stats[question_index]
                    
                    col1,col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{question_content["question"]}**")
                        st.write(self.get_correct_answer(question_content))
                        
                    with col2:
                        # st.header(question_stats['scores'])
                        st.markdown(f"**{feedback_analyses[str(question_index)]["title"]}**")
                        st.write(feedback_analyses[str(question_index)]["text"])
                        self.plot_scores(question_stats['scores'])

    def run(self):
        """
        Renders the overview page with the lecture title and the topics from the 
        lecture in seperate containers that allow the user to look at the contents
        and to select the topics they want to learn.
        """
        # Fetch module info to be rendered
        module = st.session_state.selected_module
        st.session_state.page_content = self.cont_dal.fetch_module_content(module)
        
        self.set_styling() # for texts

        self.render_title()
        # Spacing
        st.write("\n")
        
        module = st.session_state.selected_module.replace(" ", "_")
        
        topics = self.cont_dal.get_topics_list(module)
        for topic_index, topic in enumerate(topics):
            self.show_topic_feedback(module, topic)
            if topic_index > 2:
                break