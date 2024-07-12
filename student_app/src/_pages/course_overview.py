import streamlit as st
from data.data_access_layer import DatabaseAccess
from utils.utils import Utils


class CoursesOverview:
    def __init__(self):
        self.db_dal = DatabaseAccess()
        self.utils = Utils()

    def go_to_course(self, course_name):
        """
        Callback function for the button that redirects to the course overview page.
        """
        st.session_state.selected_course = course_name
        st.session_state.selected_phase = "lectures"

    def render_course_card(self, course_name, course_description):
        """
        Renders the course title and description as a button.
        """
        with st.container(border=True, height=200):
            st.subheader(course_name)
            st.write(course_description)
            st.button(
                "Selecteer cursus",
                key=course_name,
                on_click=self.go_to_course,
                args=(course_name,),
                use_container_width=True,
            )

    def render_courses(self):
        """
        Renders the course title and description as a button.
        """
        # Two columns for the courses
        cols = st.columns(2)

        for i, course in enumerate(st.session_state.courses):
            # Determine in which column the course should be placed
            if i % 2 == 0:
                # Display the course info and button to view the lectures
                with cols[0]:
                    self.render_course_card(course.title, course.description)
            else:
                with cols[1]:
                    self.render_course_card(course.title, course.description)

    def run(self):
        # Ensure this page is ran from the main controller and last visited page is displayed when user returns
        self.db_dal.update_last_phase("lectures")

        st.title("Vakken")
        self.utils.add_spacing(1)

        st.session_state.courses = self.db_dal.get_course_catalog().courses

        self.render_courses()
