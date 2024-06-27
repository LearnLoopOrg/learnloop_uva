import streamlit as st
from .topic_overview import TopicOverview
from data.data_access_layer import DatabaseAccess

class LectureOverview:
    def __init__(self):
        self.db_dal = DatabaseAccess()
        st.session_state.lectures = [("1_Embryonale_ontwikkeling", "De ontwikkeling van een embryo van bevruchting tot geboorte en de invloed van externe factoren."),
                ("2_Machine_Learning", "De fundamentele principes achter machine learning en hoe je die kunt implementern om bedrijfsprocessen te verbeteren."),
                ("3_Data_analytics", "Hoe je data kunt analyseren en visualiseren om er waardevolle inzichten uit te halen en beslissingen te ondersteunen."),
                ("4_Data_engineering", "Hoe je data pipelines kunt bouwen om data te verzamelen en te verwerkem van verschillende bronnen op grote schaal.")]
    
    def render_logo(self):
        st.image('src/data/content/images/logo.png', width=100)

    def render_sidebar(self):
        """
        Renders the contents of the sidebar, including the course buttons and login info.
        """
        with st.sidebar:

            image_col = st.columns([0.4, 1])
            with image_col[1]:
                self.render_logo()

            # Spacing
            st.write("\n\n")
            st.write("\n\n")
            st.write("\n\n")

            # Display available courses as buttons
            st.header("Vakken")
            for course in st.session_state.courses:
                st.button(course, use_container_width=True)

            # Spacing
            st.write("\n\n")
            st.write("\n\n")
            st.write("\n\n")

            # Login info & logout button
            st.write(f"**Luc Mahieu**") #TODO: HARDCODED: replace with actual username
            st.button("Uitloggen", use_container_width=True)

    def go_to_lecture(self, lecture_title):
        """
        Sets the selected page and lecture to the one that the student clicked on.
        """
        st.session_state.selected_phase = 'topics'
        st.session_state.selected_module = lecture_title
        self.db_dal.update_last_module()

    def render_page_title(self):
        title_html = open("./src/assets/html/lecture_title.html", "r").read()
        title_css = open("./src/assets/css/lecture_title.css", "r").read()
        
        st.markdown(f"<style>{title_css}</style>", unsafe_allow_html=True)
        st.markdown(title_html, unsafe_allow_html=True)

    def render_page(self):
        """
        Render the page that shows all the lectures that are available for the student for this course.
        """
        for lecture_title, lecture_description in st.session_state.lectures:
            container = st.container(border=True)
            cols = container.columns([14, 6, 1])
        
            with container:
                # Render the button to view the lecture
                with cols[1]:
                    st.write("\n\n")
                    st.button("Leerstof bekijken",
                              key=lecture_title,
                              on_click=self.go_to_lecture,
                              args=(lecture_title.replace('_', ' '),),
                              use_container_width=True
                    )
                
                # Render the lecture title and description
                with cols[0]:
                    lecture_title = lecture_title.split('_', 1)[1].replace('_', ' ')
                    st.subheader(lecture_title)
                    st.write(lecture_description)


    def run(self):
        # Ensure this page is ran from the main controller and last visited page is displayed when user returns
        self.db_dal.update_last_phase('lectures')

        self.render_page_title()

        # Spacing
        st.write("\n\n")
        st.write("\n\n")

        # self.render_sidebar()

        self.render_page()

if __name__ == "__main__":
    LectureOverview().run()
