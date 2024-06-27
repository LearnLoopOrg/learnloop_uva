import streamlit as st
from .lecture_overview import LectureOverview
from data.data_access_layer import DatabaseAccess

class CoursesOverview:
    def __init__(self):
        self.db_dal = DatabaseAccess()
        st.session_state.courses = [("AI & Data Science", "Leer over de toepassing van AI in bedrijfsstrategieën en -operaties en verdiep je in de fundamenten van AI. "),
                ("Business Analytics", "Leer hoe je data kunt analyseren en visualiseren om er waardevolle inzichten uit te halen en beslissingen te ondersteunen."),
                ("Ethical AI", "Leer over de ethische implicaties van AI en hoe je AI-projecten kunt ontwerpen en implementeren op een ethisch verantwoorde en duurzame manier.")
        ]
        self.lecture_overview = LectureOverview()
    
    def go_to_course(self, course_name):
        """
        Callback function for the button that redirects to the course overview page.
        """
        st.session_state.selected_course = course_name
        st.session_state.selected_phase = 'lectures'
    
    def run(self):
        # Ensure this page is ran from the main controller and last visited page is displayed when user returns
        self.db_dal.update_last_phase('lectures')

        st.title("Vakken")

        # Two columns for the courses
        cols = st.columns(2)

        for i, (course_name, course_description) in enumerate(st.session_state.courses):
            
            # Determine in which column the course should be placed
            if i % 2 == 0:

                # Display the course info and button to view the lectures
                with cols[0]:             
                    
                    with st.container(border=True, height=250):
                        st.header(course_name)
                        st.write(course_description)
                        st.button("Selecteer cursus", key=course_name, on_click=self.go_to_course, args=(course_name,), use_container_width=True)
            else:
                with cols[1]:
                    with st.container(border=True, height=250):
                        st.header(course_name)
                        st.write(course_description)
                        st.button("Selecteer cursus", key=course_name, on_click=self.go_to_course, args=(course_name,), use_container_width=True)