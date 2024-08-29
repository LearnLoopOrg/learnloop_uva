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

    def display_login_info(self):
        """Displays login information and logout button."""
        st.write(
            f"{st.session_state.controller.username}"
        )  # TODO: Replace with actual username
        st.button("Uitloggen", use_container_width=True)

    def go_to_lecture(self, lecture_title):
        """
        Sets the selected page and lecture to the one that the student clicked on.
        """
        st.session_state.selected_module = lecture_title
        self.utils.set_phase_to_match_lecture_status("topics")
        self.db_dal.update_last_module()

    def render_lecture(self, lecture_title, lecture_description):
        """
        Renders a single lecture's title, description, and view button.
        """
        container = st.container(border=True)
        cols = container.columns([14, 6, 1])
        with container:
            with cols[1]:
                st.write("\n\n")
                st.button(
                    "📝 Leerstof oefenen",
                    key=lecture_title,
                    on_click=self.go_to_lecture,
                    args=(lecture_title,),
                    use_container_width=True,
                )
                self.render_page_button(
                    "📚 Overzicht theorie",
                    f"{lecture_title}",
                    phase="theory-overview",
                )
            with cols[0]:
                formatted_title = lecture_title.split("_", 1)[1].replace("_", " ")
                st.subheader(formatted_title)
                st.write(lecture_description)

    def render_page_button(self, page_title, module, phase):
        """
        Renders the buttons that the users clicks to go to a certain lecture learning experience.
        """

        if st.button(
            page_title,
            key=f"{module} {phase} theory-overview button",
            use_container_width=True,
        ):
            st.session_state.selected_module = module

            self.utils.set_phase_to_match_lecture_status(phase)

            st.session_state.info_page = False
            print("Phase set to", st.session_state.selected_phase)
            self.track_visits()
            st.rerun()

    def track_visits(self):
        """Tracks the visits to the modules."""
        self.db_dal.db.users.update_one(
            {"username": st.session_state.username},
            {
                "$inc": {
                    f"progress.{st.session_state.selected_module}.visits.{st.session_state.selected_phase}": 1
                }
            },
        )

    def render_page(self):
        """
        Render the page that shows all the lectures that are available for the student for this course.
        """
        for lecture in st.session_state.lectures:
            self.render_lecture(lecture.title, lecture.description)

    def load_lectures(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.db_dal.get_course_catalog(
            file_path="./src/data/uva_dummy_db.json"
        )
        if st.session_state.selected_course is None:
            st.session_state.selected_course = course_catalog.courses[0].title

        print("Selected course:", st.session_state.selected_course)
        st.session_state.lectures = self.db_dal.get_lectures_for_course(
            st.session_state.selected_course, course_catalog
        )

    def run(self):
        self.db_dal.update_last_phase("lectures")
        self.load_lectures()
        st.title("Collegeoverzicht")
        self.utils.add_spacing(1)
        self.render_page()


if __name__ == "__main__":
    LectureOverview().run()
