from datetime import datetime
from typing import Any
from slack_sdk import WebClient
import streamlit as st


class ModuleRepository:
    def __init__(self):
        pass

    def save_draft_correction(self, module, updated_segments):
        self._save_topics_json(module, updated_segments)
        st.session_state.db.get_collection("content").find_one_and_update(
            {"lecture_name": module},
            {
                "$set": {
                    "status": "generated",
                    "updated_at": datetime.now(),
                    "corrected_lecturepath_content": {"segments": updated_segments},
                }
            },
        )
        return

    def save_final_correction(self, module, updated_segments):
        self._save_topics_json(module, updated_segments)
        updated_segments = self.remove_topics_from_updated_segments(updated_segments)
        st.session_state.db.get_collection("content").find_one_and_update(
            {"lecture_name": module},
            {
                "$set": {
                    "status": "corrected",
                    "updated_at": datetime.now(),
                    "corrected_lecturepath_content": {"segments": updated_segments},
                }
            },
        )
        return

    def remove_topics_from_updated_segments(self, updated_segments):
        for segment in updated_segments:
            if "topic_title" in segment:
                del segment["topic_title"]
        return updated_segments

    def _save_topics_json(self, module, updated_segments):
        topics_dict = {}

        # Iterate over the segments to group them by topic_title
        for index, segment in enumerate(updated_segments):
            topic_title = segment.get("topic_title", "Unknown Topic")
            if topic_title not in topics_dict:
                topics_dict[topic_title] = {
                    "topic_title": topic_title,
                    "segment_indexes": [],
                }
            topics_dict[topic_title]["segment_indexes"].append(index)
        # Convert the topics_dict to a list of topics
        topics_json = {"topics": list(topics_dict.values())}
        self._save_topics_json_to_db(module, topics_json)

    def _save_topics_json_to_db(self, module, topics_json):
        st.session_state.db.get_collection("content").find_one_and_update(
            {"lecture_name": module},
            {
                "$set": {
                    "corrected_lecturepath_topics": topics_json,
                    "updated_at": datetime.now(),
                }
            },
        )

    def _update_correct_lecture_path_content(
        self, module, segments_list_with_delete
    ) -> None:
        modules_segments_list = []

        for segment in segments_list_with_delete:
            if segment["delete"] == "no":
                modules_segment = segment.copy()
                del modules_segment["delete"]
                modules_segments_list.append(modules_segment)

        print("Updating segments list with length ", len(modules_segments_list))

        st.session_state.db.get_collection("content").find_one_and_update(
            {"lecture_name": module},
            {
                "$set": {
                    "corrected_lecturepath_content": {
                        "segments": modules_segments_list
                    },
                    "updated_at": datetime.now(),
                }
            },
        )

    def get_content_from_db(self, module: str):
        doc = st.session_state.db.get_collection("content").find_one(
            {"lecture_name": module}
        )
        if doc is None:
            raise ValueError(f"Module {module} not found in database")
        return doc

    def exception_handler(self, error_message: str) -> None:
        # Custom error handling
        BOT_OAUTH_TOKEN = "xoxb-7362589208226-7719097315238-curwvsQxH1PbDjnQGQstR3JN"
        try:
            client = WebClient(token=BOT_OAUTH_TOKEN)
            client.chat_postMessage(
                channel="production-errors-student-app",
                text=f"An error occurred in the student app: {error_message}",
                username="Bot User",
            )
        except Exception as e:
            print(e)
            pass

    def _upload_modules_topics_json(self, module, segments_list) -> None:
        modules_topics_topics_list = []

        module_content = self.get_content_from_db(module)
        topics = module_content["original_lecturepath_topics"]["topics"]

        topic_id = 0
        topic_segment_id = 0
        topic_segment_id_new = 0
        topic_segment_id_list = []

        # DEBUGGING. segments list should be equal to the length of all segments indices of topics
        len_segments_list = len(segments_list)
        len_segments_indices = sum([len(topic["segment_indexes"]) for topic in topics])

        if len_segments_list != len_segments_indices:
            error_message = (
                f"Number of segments in the list {len_segments_list} does not match the number of segments "
                f"in the topics {len_segments_indices}"
            )
            self.exception_handler(error_message)

        for segment in segments_list:
            topic_title = topics[topic_id]["topic_title"]

            if segment["delete"] == "no":
                topic_segment_id_list.append(topic_segment_id_new)
                topic_segment_id_new += 1

            if topic_segment_id == len(topics[topic_id]["segment_indexes"]) - 1:
                modules_topics_topics_list.append(
                    {
                        "topic_title": topic_title,
                        "segment_indexes": topic_segment_id_list,
                    }
                )
                topic_id += 1
                topic_segment_id = 0
                topic_segment_id_list = []
            else:
                topic_segment_id += 1

        st.session_state.db.get_collection("content").find_one_and_update(
            {"lecture_name": module},
            {
                "$set": {
                    "corrected_lecturepath_topics": {
                        "topics": modules_topics_topics_list,
                        "updated_at": datetime.now(),
                    }
                }
            },
        )
