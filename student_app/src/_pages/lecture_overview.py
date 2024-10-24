import streamlit as st


class LectureOverview:
    def __init__(self):
        pass

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

    def go_to_lecture(self, lecture_title, new_phase):
        """
        Sets the selected page and lecture to the one that the student clicked on.
        """
        st.session_state.selected_module = lecture_title
        self.utils.set_phase_to_match_lecture_status(new_phase)

        self.db_dal.update_last_module()

    def render_lecture(self, lecture_title, lecture_description, lecture_record):
        """
        Renders a single lecture's title, description, and view button.
        """
        container = st.container(border=True)
        cols = container.columns([14, 6, 1])
        st.session_state.selected_module = lecture_title

        with container:
            role = st.session_state.username["role"]
            lecture_status = (
                lecture_record["status"] if lecture_record else "not_recorded"
            )

            with cols[1]:
                st.write("\n\n")

                print("role: ", role)
                print("lecture_status: ", lecture_status)

                match role, lecture_status:
                    case "teacher", "not_recorded":
                        self.render_page_button(
                            "⏳ Nog niet beschikbaar",
                            lecture_title,
                            phase="not_recorded",
                        )

                    case "teacher", "corrected":
                        self.render_page_button(
                            "📊 Inzichten bekijken",
                            lecture_title,
                            phase="insights",
                        )

                    case "teacher", "generated":
                        self.render_page_button(
                            "✔️ Kwaliteitscheck",
                            lecture_title,
                            phase="quality-check",
                        )

                    case "student", "not_recorded" | "generated":
                        self.render_page_button(
                            "⏳ Nog niet beschikbaar",
                            lecture_title,
                            phase="not_recorded",
                        )

                    case "student", "corrected":
                        self.render_page_button(
                            "📝 Leerstof oefenen",
                            f"{lecture_title}",
                            phase="learning",
                        )
                        self.render_page_button(
                            "📚 Overzicht theorie",
                            f"{lecture_title}",
                            phase="theory-overview",
                        )
                        if st.session_state.username["name"] == "supergeheimecode":
                            self.render_page_button(
                                "📝 Socratisch dialoog",
                                f"{lecture_title}",
                                phase="socratic-dialogue",
                            )

            with cols[0]:
                st.subheader(lecture_title)
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
            self.track_visits()
            st.rerun()

    def track_visits(self):
        """Tracks the visits to the modules."""
        self.db.users.update_one(
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
            # find the lecture that is currently being rendered in the database
            lecture_record = self.db_dal.get_lecture(lecture.title)
            self.render_lecture(lecture.title, lecture.description, lecture_record)

    def load_lectures(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.db_dal.get_course_catalog()
        print("course_catalog: ", course_catalog)
        if st.session_state.selected_course is None:
            print("selected_course is None")
            st.session_state.selected_course = course_catalog.courses[0].title

        st.session_state.lectures = self.db_dal.get_lectures_for_course(
            st.session_state.selected_course, course_catalog
        )
        print("lectures: ", st.session_state.lectures)

    def run(self):
        self.db_dal = st.session_state.db_dal
        self.utils = st.session_state.utils
        self.db = st.session_state.db

        self.db_dal.update_last_phase("lectures")

        self.load_lectures()
        st.title("Moduleoverzicht")
        self.utils.add_spacing(1)
        self.render_page()


if __name__ == "__main__":
    LectureOverview().run()
