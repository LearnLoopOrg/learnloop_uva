from api.module import ModuleRepository
from data.data_access_layer import DatabaseAccess
from utils.utils import ImageHandler, Utils
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class QualityCheck:
    def __init__(self):
        self.utils = Utils()
        self.module_repository = ModuleRepository(st.session_state.db)
        self.db_dal = DatabaseAccess()
        self.image_handler = ImageHandler()
        self.module_name = st.session_state.selected_module

        self._initialise_segments_in_qualitycheck()

    def _initialise_segments_in_qualitycheck(self):
        content = self.db_dal.fetch_corrected_module_content(self.module_name)
        if content == "":
            content = self.db_dal.fetch_original_module_content(self.module_name)
        self.segments = content["segments"]

        topics = self.db_dal.fetch_original_module_topics(self.module_name)
        if topics == "":
            topics = self.db_dal.fetch_corrected_module_topics(self.module_name)
        self.topics = topics["topics"]
        for topic in self.topics:
            topic_title = topic["topic_title"]
            segment_indexes = topic["segment_indexes"]
            for idx in segment_indexes:
                if idx < len(self.segments):
                    self.segments[idx]["topic_title"] = topic_title
                else:
                    print(f"Warning: segment index {idx} is out of range")

        st.session_state.segments_in_qualitycheck = self.segments

    def run(self):
        self.db_dal.update_last_phase("quality_check")
        self.display_segments()
        self.display_save_buttons()

    def display_save_buttons(self):
        if st.button("Tussentijds opslaan", use_container_width=True):
            self.save_updates_in_session_state()
            self.module_repository.save_draft_correction(
                st.session_state.selected_module,
                st.session_state.segments_in_qualitycheck,
            )
        if st.button("Definitief opslaan", use_container_width=True):
            self.save_updates_in_session_state()
            self.module_repository.save_final_correction(
                st.session_state.selected_module,
                st.session_state.segments_in_qualitycheck,
            )
            st.rerun()

    def display_segments(self):
        segments = st.session_state.segments_in_qualitycheck
        for segment_id, segment in enumerate(segments):
            with st.container(border=True):
                self.display_segment(segment_id, segment)

    def display_segment(self, segment_id, segment):
        flagged_for_deletion = segment.get("flagged_for_deletion")
        if segment.get("flagged_for_deletion"):
            st.warning("Dit segment is gemarkeerd voor verwijdering.")

        # Add Delete/Undo Delete button
        delete_button_key = f"delete_button_{segment_id}"
        if not flagged_for_deletion:
            if st.button("Verwijderen", key=delete_button_key):
                st.session_state.segments_in_qualitycheck[segment_id][
                    "flagged_for_deletion"
                ] = True
                st.rerun()
        else:
            if st.button("Verwijderen ongedaan maken", key=delete_button_key):
                del st.session_state.segments_in_qualitycheck[segment_id][
                    "flagged_for_deletion"
                ]
                st.rerun()

        if segment.get("image"):
            self.image_handler.render_image(segment, max_height=300)

        self.display_segment_content(segment_id, segment)

    def display_segment_content(self, segment_id, segment):
        segment_type = segment["type"]
        if segment_type == "theory":
            self.display_theory_segment(segment_id, segment)
        elif segment_type == "question" and "answers" not in segment:
            self.display_question_segment(segment_id, segment)
        elif segment_type == "question" and segment.get("subtype") == "mc_question":
            self.display_MC_question(segment_id, segment)

    def display_theory_segment(self, segment_id, segment):
        st.markdown("### Theorie segment")
        title_key = f"segment_{segment_id}_title"
        text_key = f"segment_{segment_id}_text"
        st.text_area("Titel", value=segment.get("title", ""), key=title_key)
        st.text_area("Theorie", value=segment.get("text", ""), key=text_key)

    def display_question_segment(self, segment_id, segment):
        st.markdown("### Open Vraag")
        question_key = f"segment_{segment_id}_question"
        answer_key = f"segment_{segment_id}_answer"
        st.text_area("Vraag", value=segment.get("question", ""), key=question_key)
        st.text_area("Antwoord", value=segment.get("answer", ""), key=answer_key)

    def display_MC_question(self, segment_id, segment):
        st.markdown("### Meerkeuzevraag")
        question_key = f"segment_{segment_id}_question"
        correct_answer_key = f"segment_{segment_id}_correct_answer"
        wrong_answers_key = f"segment_{segment_id}_wrong_answers"
        st.text_area("Vraag", value=segment.get("question", ""), key=question_key)
        st.text_area(
            "Goede antwoord",
            # value=", ".join(segment.get("answers", [])),
            value=segment.get("answers").get("correct_answer"),
            key=correct_answer_key,
        )
        st.text_area(
            "Foute antwoord(en)",
            value="\n".join(segment.get("answers").get("wrong_answers")),
            key=wrong_answers_key,
        )
        st.text_area

    def save_updates_in_session_state(self):
        segments = st.session_state.segments_in_qualitycheck
        updated_segments = []
        for segment_id, segment in enumerate(segments):
            if segment.get("flagged_for_deletion"):
                # Skip this segment; it will not be included in the updated_segments
                continue
            segment_type = segment["type"]
            if segment_type == "theory":
                title_key = f"segment_{segment_id}_title"
                text_key = f"segment_{segment_id}_text"
                updated_title = st.session_state.get(
                    title_key, segment.get("title", "")
                )
                updated_text = st.session_state.get(text_key, segment.get("text", ""))
                segment["title"] = updated_title
                segment["text"] = updated_text
            elif segment_type == "question" and "answers" not in segment:
                question_key = f"segment_{segment_id}_question"
                answer_key = f"segment_{segment_id}_answer"
                updated_question = st.session_state.get(
                    question_key, segment.get("question", "")
                )
                updated_answer = st.session_state.get(
                    answer_key, segment.get("answer", "")
                )
                segment["question"] = updated_question
                segment["answer"] = updated_answer
            elif segment_type == "question" and segment.get("subtype") == "mc_question":
                question_key = f"segment_{segment_id}_question"
                correct_answer_key = f"segment_{segment_id}_correct_answer"
                wrong_answers_key = f"segment_{segment_id}_wrong_answers"

                updated_question = st.session_state.get(
                    question_key, segment.get("question", "")
                )
                updated_correct_answer = st.session_state.get(
                    correct_answer_key,
                    segment.get("answers", {}).get("correct_answer", ""),
                )
                updated_wrong_answers_text = st.session_state.get(
                    wrong_answers_key,
                    "\n".join(segment.get("answers", {}).get("wrong_answers", [])),
                )
                updated_wrong_answers = [
                    answer.strip()
                    for answer in updated_wrong_answers_text.split("\n")
                    if answer.strip()
                ]

                segment["question"] = updated_question
                segment["answers"] = {
                    "correct_answer": updated_correct_answer,
                    "wrong_answers": updated_wrong_answers,
                }
            updated_segments.append(segment)
        # Update the session state with the modified segments
        st.session_state.segments_in_qualitycheck = updated_segments

        st.success("Voortgang opgeslagen.")

    def display_header(self):
        st.title(f"Kwaliteitscheck: {st.session_state.selected_module}")
        st.write(
            "Controleer de onderstaande gegenereerde oefenmaterialen om er zeker van te zijn dat studenten het juiste leren. "
            "Pas de afbeelding, theorie, vraag of het antwoord aan, of verwijder deze indien nodig. "
            "Als je klaar bent, kun je de oefenmaterialen direct delen met studenten door op de button onderaan te drukken."
        )


if __name__ == "__main__":
    qc = QualityCheck()
    qc.run()
