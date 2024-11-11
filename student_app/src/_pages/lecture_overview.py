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

    def update_module_and_phase(self, lecture_title, new_phase):
        """
        Sets the selected page and lecture to the one that the student clicked on.
        """
        st.session_state.selected_module = lecture_title
        st.session_state.selected_phase = new_phase

        self.db_dal.update_last_module()
        self.db_dal.update_last_phase(new_phase)

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
                lecture_record["status"] if lecture_record else "not-recorded"
            )

            with cols[1]:
                st.write("\n\n")

                print("role: ", role)
                print("lecture_status: ", lecture_status)

                match role, lecture_status:
                    case "teacher", "not-recorded":
                        st.button(
                            "⏳ Nog niet beschikbaar",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "not-recorded"),
                            use_container_width=True,
                            key=lecture_title + "_not-recorded",
                        )

                    case "teacher", "corrected":
                        st.button(
                            "📊 Inzichten bekijken",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "insights"),
                            use_container_width=True,
                            key=lecture_title + "_insights",
                        )

                    case "teacher", "generated":
                        st.button(
                            "✔️ Kwaliteitscheck",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "quality-check"),
                            use_container_width=True,
                            key=lecture_title + "_quality-check",
                        )

                    case "student", "not-recorded" | "generated":
                        st.button(
                            "⏳ Nog niet beschikbaar",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "not-recorded"),
                            use_container_width=True,
                            key=lecture_title + "_not-recorded",
                        )

                    case "student", "corrected":
                        st.button(
                            "📝 Leerstof oefenen",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "topics"),
                            use_container_width=True,
                            key=lecture_title + "_topics",
                        )
                        st.button(
                            "📚 Overzicht theorie",
                            on_click=self.update_module_and_phase,
                            args=(lecture_title, "theory-overview"),
                            use_container_width=True,
                            key=lecture_title + "_theory-overview",
                        )
                        if st.session_state.username["name"] == "supergeheimecode":
                            st.button(
                                "📝 Socratisch dialoog",
                                on_click=self.update_module_and_phase,
                                args=(lecture_title, "socratic-dialogue"),
                                use_container_width=True,
                                key=lecture_title + "_socratic-dialogue",
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
            key=f"module_{module}_phase_{phase}",
            use_container_width=True,
        ):
            st.session_state.selected_module = module
            st.session_state.selected_phase = phase

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

    def load_lectures_in_session_state(self):
        """
        Loads lectures from the database into the session state.
        """
        course_catalog = self.db_dal.get_course_catalog()
        if st.session_state.selected_course is None:
            print("selected_course from catalog ", course_catalog.courses[0].title)
            st.session_state.selected_course = course_catalog.courses[0].title

        print("selected_course: ", st.session_state.selected_course)

        # lectures = course_catalog.courses[0].lectures

        # st.session_state.lectures = [
        #     lecture.title for lecture in lectures if lecture.title is not None
        # ]
        # print("lectures zelf uit de catalog gehaald: ", st.session_state.lectures)
        st.session_state.lectures = self.db_dal.get_lectures_for_course(
            st.session_state.selected_course, course_catalog
        )

    def render_lectures(self):
        """
        Renders the lectures in the session state.
        """
        # Check if there are lectures loaded in the session state
        if not st.session_state.lectures:
            st.write("Er zijn geen colleges beschikbaar voor deze cursus.")
            return

        # Loop through each lecture and render it
        for lecture in st.session_state.lectures:
            try:
                lecture_record = st.session_state.db.content.find_one(
                    {"lecture_name": str(lecture.title)}
                )
                self.render_lecture(lecture.title, lecture.description, lecture_record)
            except Exception as e:
                st.error(
                    f"Er is een fout opgetreden bij het laden van college '{lecture.title}': {e}"
                )

    def run(self):
        self.db_dal = st.session_state.db_dal
        self.utils = st.session_state.utils
        self.db = st.session_state.db
        self.db_dal.update_last_phase("lectures")

        st.title("Moduleoverzicht")
        st.write("\n\n")

        self.load_lectures_in_session_state()
        self.render_lectures()


if __name__ == "__main__":
    LectureOverview().run()
