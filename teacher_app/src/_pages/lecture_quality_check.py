from utils.utils import *
import streamlit as st
from dotenv import load_dotenv
import json

load_dotenv()

class QualityCheck:
    def __init__(self):
        self.lecture_number, self.lecture_name = st.session_state.selected_module.split(' ', 1)
        self.utils = Utils()
    
    def run(self):
        print(f"Quality check for lecture {self.lecture_number} started")
        st.title(f"Kwaliteitscheck college {self.lecture_number}:")
        st.subheader(self.lecture_name)

        st.write("Controleer de onderstaande gegenereerde oefenmaterialen om er zeker van te zijn dat studenten het juiste leren. Pas de afbeelding, theorie, vraag of het antwoord aan, of verwijder deze indien nodig. Als je klaar bent, kun je de oefenmaterialen direct delen met studenten door op de button onderaan te drukken.")

        with open(f'src/data/content/modules/{st.session_state.selected_module.replace(" ", "_")}.json') as f:
            data_modules = json.load(f)

        with open(f'src/data/content/topics/{st.session_state.selected_module.replace(" ", "_")}_topics.json') as g:
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

        if st.button("Opslaan", use_container_width=True):
            self.utils.upload_json(st.session_state.selected_module.replace(" ", "_"))