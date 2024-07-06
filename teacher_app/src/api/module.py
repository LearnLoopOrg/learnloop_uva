from datetime import datetime
import json
from typing import Any
from pymongo.database import Database


class ModuleRepository:
    def __init__(self, db: Database[dict[str, Any]]):
        self.db = db

    # TODO: update state on correction
    def update_status(self, module, status) -> None:
        pass

    def update_correct_lecture_path_content(
        self, module, segments_list_with_delete
    ) -> None:
        modules_segments_list = []

        for segment in segments_list_with_delete:
            if segment["delete"] == "no":
                modules_segment = segment.copy()
                del modules_segment["delete"]
                modules_segments_list.append(modules_segment)

        print("Updating segments list with length ", len(modules_segments_list))

        self.db.get_collection("content").find_one_and_update(
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
        doc = self.db.get_collection("content").find_one({"lecture_name": module})
        if doc is None:
            raise ValueError(f"Module {module} not found in database")
        return doc

    def upload_modules_topics_json(
        self, module: str, segments_with_delete: list
    ) -> None:
        module_content = self.get_content_from_db(module)
        topics = module_content["original_lecturepath_topics"]["topics"]

        topic_segment_id = 0
        topic_segment_id_new = 0
        topic_segment_id_list = []
        modules_topics_topics_list = []

        # DEBUGGING. segments list should be equal to the length of all segments indices of topics
        len_segments_list = len(segments_with_delete)
        len_segments_indices = sum([len(topic["segment_indexes"]) for topic in topics])
        if len_segments_list != len_segments_indices:
            raise ValueError(
                f"Number of segments in the list {len_segments_list} does not match the number of segments in the topics {len_segments_indices}"
            )

        for i, segment in enumerate(segments_with_delete):
            topic_segments = topics[i]["segment_indexes"]

            if topic_segment_id == len(topic_segments) - 1:
                modules_topics_topics_list.append(
                    {
                        "topic_title": topics[i]["topic_title"],
                        "segment_indexes": topic_segment_id_list,
                    }
                )
                topic_segment_id = 0
                topic_segment_id_list = []
            if segment["delete"] == "yes":
                topic_segment_id_list

            if segment["delete"] == "no":
                topic_segment_id_list.append(topic_segment_id_new)
                topic_segment_id_new += 1

            else:
                topic_segment_id += 1

        self.db.get_collection("content").find_one_and_update(
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
