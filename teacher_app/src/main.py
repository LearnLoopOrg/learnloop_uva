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
from _pages.lecture_student_answers_insights import LectureInsights
from _pages.lecture_quality_check import QualityCheck

# Must be called first
st.set_page_config(page_title="LearnLoop", layout="wide")

load_dotenv()

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
        elif st.session_state.selected_phase == 'record': #TODO: Connect merge and connect record page
            # self.record_page.run()
            pass
        elif st.session_state.selected_phase == 'quality_check':
            self.quality_check_page.run()
        elif st.session_state.selected_phase == 'insights':
            self.insights_page.run()


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