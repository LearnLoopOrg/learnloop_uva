import streamlit as st
from data.data_access_layer import DatabaseAccess
from utils.utils import Utils


class LectureOverview:
    def __init__(self):
        self.db_dal = DatabaseAccess()
        self.utils = Utils()

    def display_courses(self):
        """Displays available courses as buttons."""
        st.header("Mijn vakken")
        for course in st.session_state.courses:
            st.button(course, use_container_width=True)

    def go_to_lecture(self, lecture_title):
        """
        Sets the selected page and lecture to the one that the student clicked on.
        """
        st.session_state.selected_module = lecture_title
        module_status = self.db_dal.fetch_module_status()

        if module_status == "corrected":
            st.session_state.selected_phase = "insights"
        elif module_status == "generated":
            st.session_state.selected_phase = "quality_check"
        elif module_status == "not_recorded":
            st.session_state.selected_phase = "record"

        self.db_dal.update_last_module()

    def render_page(self):
        """
        Render the page that shows all the lectures that are available for the student for this course.
        """
        for lecture in st.session_state.lectures:
            self.render_lecture(lecture)

    def render_lecture(self, lecture):
        container = st.container(border=True)
        cols = container.columns([14, 6, 1])
        with container:
            # Render the button to view the lecture
            with cols[1]:
                st.write("\n\n")
                st.session_state.selected_module = lecture.title

                module_status = self.db_dal.fetch_module_status()

                if module_status is None:
                    module_status = "not_recorded"

                match module_status:
                    case "corrected":
                        st.button(
                            "📊 Inzichten bekijken",
                            key=lecture.title,
                            on_click=self.go_to_lecture,
                            args=(lecture.title,),
                            use_container_width=True,
                        )
                    case "generated":
                        st.button(
                            "✔️ Kwaliteitscheck",
                            key=lecture.title,
                            on_click=self.go_to_lecture,
                            args=(lecture.title,),
                            use_container_width=True,
                        )
                    case "not_recorded":
                        st.button(
                            # "Genereren leermateriaal",
                            "⏳ Nog niet beschikbaar",
                            key=lecture.title,
                            on_click=self.go_to_lecture,
                            args=(lecture.title,),
                            use_container_width=True,
                        )

            with cols[0]:
                internal_cols = st.columns([0.5, 40])
                with internal_cols[1]:
                    st.subheader(lecture.title)
                    st.write(lecture.description)

    def load_lectures(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.db_dal.get_course_catalog()
        if st.session_state.selected_course is None:
            st.session_state.selected_course = course_catalog.courses[0].title

        st.session_state.lectures = self.db_dal.get_lectures_for_course(
            st.session_state.selected_course, course_catalog
        )

    def run(self):
        self.db_dal.update_last_phase("lectures")
        self.load_lectures()
        st.title("Moduleoverzicht")
        self.utils.add_spacing(1)
        self.render_page()


if __name__ == "__main__":
    LectureOverview().run()
