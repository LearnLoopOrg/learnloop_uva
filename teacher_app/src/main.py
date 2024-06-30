from utils.utils import *
from utils.openai_client import connect_to_openai
import time
import random
import streamlit as st
from dotenv import load_dotenv
import os
import json
from openai import AzureOpenAI
from openai import OpenAI
from pymongo import MongoClient
import base64
import utils.db_config as db_config
from data.data_access_layer import DatabaseAccess, ContentAccess
from datetime import datetime
from _pages.lecture_overview import LectureOverview
from _pages.course_overview import CoursesOverview
from _pages.lecture_insights import LectureInsights

# Must be called first
st.set_page_config(page_title="LearnLoop", layout="wide")

load_dotenv()

class QualityCheck:
    def __init__(self):
        self.module = st.session_state.selected_module
        self.lecture_number, self.lecture_name = self.module.split(' ', 1)
        self.utils = Utils()
    
    def run(self):
        st.title(f"Kwaliteitscheck college {self.lecture_number}:")
        st.subheader(self.lecture_name)

        st.write("Controleer de onderstaande gegenereerde oefenmaterialen om er zeker van te zijn dat studenten het juiste leren. Pas de afbeelding, theorie, vraag of het antwoord aan, of verwijder deze indien nodig. Als je klaar bent, kun je de oefenmaterialen direct delen met studenten door op de button onderaan te drukken.")

        with open(f'src/data/modules/{self.module}.json') as f:
            data_modules = json.load(f)

        with open(f'src/data/modules/topics/{self.module}_topics.json') as g:
            data_modules_topics = json.load(g)

        segments = data_modules['segments']
        topics = data_modules_topics['topics']
        topic_id = 0
        topic_segment_id = 0

        for segment_id, segment in enumerate(segments):
            segment_id=str(segment_id)
            segment_type = segment["type"]
            if segment_type == "theory":
                if segment_id not in st.session_state:
                    st.session_state[segment_id] = segment["text"]
                if "new-"+segment_id not in st.session_state:
                    st.session_state["new-"+segment_id] = ""
            elif segment_type == "question":
                if segment_id not in st.session_state:
                    st.session_state[segment_id] = segment["question"]
                if "new-"+segment_id not in st.session_state:
                    st.session_state["new-"+segment_id ] = ""
                if "answers" in segment:
                    if segment_id+"-answers-correct_answer" not in st.session_state:
                        st.session_state[segment_id+"-answers-correct_answer" ] = segment["answers"]["correct_answer"]
                    if segment_id+"-answers-wrong_answers" not in st.session_state:
                        wrong_answers_enumeration = self.utils.list_to_enumeration( segment["answers"]["wrong_answers"])
                        st.session_state[segment_id+"-answers-wrong_answers" ] = wrong_answers_enumeration
                    if "new-"+segment_id+"-answers-correct_answer" not in st.session_state:
                        st.session_state[ "new-"+segment_id+"-answers-correct_answer" ] = ""
                    if "new-"+segment_id+"-answers-wrong_answers" not in st.session_state:
                        st.session_state[  "new-"+segment_id+"-answers-wrong_answers" ] = ""
                elif "answer" in segment:
                    if segment_id+"-answer" not in st.session_state:
                        st.session_state[segment_id+"-answer"] = segment["answer"]
                    if "new-"+segment_id+"-answer" not in st.session_state:
                        st.session_state["new-"+segment_id+"-answer"]= ""


        for segment_id, segment in enumerate(segments):
            if topic_segment_id == 0:
                st.subheader(topics[topic_id]["topic_title"])
            segment_id = str(segment_id)
            segment_type = segment["type"]
            with st.container(border=True):
                if segment["image"]:
                    st.image(f'src/data/images/{segment["image"]}')
                
                if segment_type == "theory":
                    st.markdown(f"**Theorie: {segment["title"]}**")
                    st.text_area( "Theorie", height=200, key=segment_id, on_change=self.utils.save_st_change( "new-"+segment_id, segment_id), label_visibility="collapsed")
                elif segment_type == "question":
                    st.markdown("**Vraag:**")
                    st.text_area( "Vraag", height=200,key=segment_id,   on_change=self.utils.save_st_change( "new-"+segment_id, segment_id), label_visibility="collapsed")
                    if "answers" in segment:
                        st.markdown("*Correct antwoord:*")
                        st.text_area(  "Correct antwoord:"  , height=200, key=segment_id+"-answers-correct_answer", on_change=self.utils.save_st_change("new-"+segment_id+"-answers-correct_answer", segment_id+"-answers-correct_answer"), label_visibility="collapsed")
                        st.markdown("*Onjuiste antwoorden:*")
                        st.text_area( "Onjuiste antwoorden:", height=200, key=segment_id+"-answers-wrong_answers", on_change=self.utils.save_st_change("new-"+segment_id+"-answers-wrong_answers", segment_id+"-answers-wrong_answers"), label_visibility="collapsed" )
                    elif "answer" in segment:
                        st.markdown("*Antwoord:*")
                        st.text_area( "Antwoord:", height=200, key= segment_id+"-answer", on_change=self.utils.save_st_change("new-"+segment_id+"-answer", segment_id+"-answer"), label_visibility="collapsed")
            
            if topic_segment_id == len(topics[topic_id]["segment_indexes"])-1:
                topic_id += 1
                topic_segment_id = 0
            else:
                topic_segment_id += 1

        if st.button("Opslaan"):
            self.utils.upload_json(self.module)

# @st.cache_resource(show_spinner=False)
class Controller:
    def __init__(_self):
        _self.initialise_session_states()
        # OpenAI & database
        st.session_state.openai_client = connect_to_openai(llm_model='gpt-4o')
        st.session_state.use_mongodb = True
        st.session_state.db = db_config.connect_db(use_mongodb=st.session_state.use_mongodb)

        # User
        st.session_state.username = 'test_user_6'
        
        # Data access layer
        _self.db_dal = DatabaseAccess()
        _self.cont_dal = ContentAccess()

        # Fetch were user left off
        st.session_state.selected_module = _self.db_dal.fetch_last_module()
        st.session_state.selected_phase = _self.db_dal.fetch_last_phase()

        # Pages
        _self.lectures_page = LectureOverview()
        _self.courses_page = CoursesOverview()
        _self.insights_page = LectureInsights()
        _self.quality_check_page = QualityCheck()

    def initialise_session_states(self):
        if 'selected_phase' not in st.session_state:
            st.session_state.selected_phase = None
        if 'selected_module' not in st.session_state:
            st.session_state.selected_module = None
        if 'openai_client' not in st.session_state:
            st.session_state.openai_client = None
        if 'use_mongodb' not in st.session_state:
            st.session_state.use_mongodb = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'db' not in st.session_state:
            st.session_state.db = None

    def render_page(self):
        """
        Determines what type of page to display based on which module the user selected.
        """
        # Determine what type of page to display
        if st.session_state.selected_phase == 'courses':
            self.courses_page.run()
        elif st.session_state.selected_phase == 'lectures':
            self.lectures_page.run()
        elif st.session_state.selected_phase == 'insights':
            self.insights_page.run()
        elif st.session_state.selected_phase == 'quality_check':
            self.quality_check_page.run()


    def render_sidebar(self):
        with st.sidebar:
            spacer, image_col = st.columns([0.4, 1])
            with image_col:
                self.render_logo()

            st.title("Navigatie")
            st.button("Vakken", on_click=self.set_selected_phase, args=('courses',), use_container_width=True)
            st.button("Colleges", on_click=self.set_selected_phase, args=('lectures',), use_container_width=True)

        
    def render_logo(self):
        st.image('src/data/content/images/logo.png', width=100)


    def set_selected_phase(self, phase):
        st.session_state.selected_phase = phase
  

if __name__=="__main__":

    if 'controller' not in st.session_state:
        st.session_state.controller = Controller()
    
    st.session_state.controller.render_sidebar()
    st.session_state.controller.render_page()