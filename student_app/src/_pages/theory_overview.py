import streamlit as st


class TheoryOverview:
    def __init__(self) -> None:
        pass

    def set_styling(self):
        st.markdown(
            """
            <style>
            .size-4 {
                font-size:20px !important;
                font-weight: bold;
            }
            .size-4-question {
                font-size: 16px !important;
                font-weight: bold;
                font-style: bold;
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render_title(self):
        st.title(f"Theorie overzicht: {st.session_state.selected_module}")
        st.write("\n")

    def render_theory_for_segments(_self, segment_indices: list[int]):
        for i in segment_indices:
            segment = _self.content["segments"][i]
            content_container = st.container()
            content_cols = content_container.columns([1, 1])

            if segment["type"] == "theory":
                # Create invisible container to cluster each infosegment with the corresponding question segment(s) and image

                with content_cols[0]:
                    title = segment["title"]
                    text = segment["text"]
                    # Write the theory contents
                    st.markdown(
                        f'<p class="size-4">{title}</p>', unsafe_allow_html=True
                    )
                    st.write(text)

                with content_cols[1]:
                    if "image" in segment:
                        if segment["image"] is not None:
                            st.session_state.image_handler.render_image(
                                segment, max_height=300
                            )

            elif segment["type"] == "question":
                with content_cols[0]:
                    question = segment["question"]
                    st.markdown(
                        f'<p class="size-4-question">{question}</p>',
                        unsafe_allow_html=True,
                    )

                    # Render normal or MC answer
                    if answer := segment.get("answer"):
                        st.write(f"_{answer}_")
                    elif mc_answers := segment.get("answers"):
                        st.write(f"_{mc_answers['correct_answer']}_")

    def run(self):
        """
        Renders the overview page with the lecture title and the topics from the
        lecture in seperate containers that allow the user to look at the contents
        and to select the topics they want to learn.
        """
        self.db_dal = st.session_state.db_dal
        self.base_path = st.session_state.base_path
        self.render_title()

        self.set_styling()  # for texts
        self.db_dal.update_last_phase("theory-overiew")

        self.topics = self.db_dal.fetch_module_topics(st.session_state.selected_module)
        self.content = self.db_dal.fetch_module_content(
            st.session_state.selected_module
        )

        for topic in self.topics["topics"]:
            st.header(topic["topic_title"])
            segment_indices: list[int] = topic["segment_indexes"]
            self.render_theory_for_segments(segment_indices)

        # Spacing
        st.write("\n")
