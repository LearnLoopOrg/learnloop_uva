from utils.utils import Utils
import streamlit as st
import time
from dotenv import load_dotenv
from data.data_access_layer import DatabaseAccess

# import numpy as np
# import cv2
# import mss
# import threading
# import wave
# import pyaudio
# import io
# import os
# import requests


load_dotenv()


class Recorder:
    def __init__(self):
        # self.container_name_video = "video"
        # self.blob_name_video = "video_output.avi"
        # self.container_name_audio = "audio"
        # self.blob_name_audio = "video_output.mp3"
        self.utils = Utils()
        self.db_dal = DatabaseAccess()

    # def record_audio(self, duration):
    #     format = pyaudio.paInt16
    #     channels = 2
    #     rate = 44100
    #     chunk = duration * rate

    #     p = pyaudio.PyAudio()

    #     stream = p.open(
    #         format=format,
    #         channels=channels,
    #         rate=rate,
    #         input=True,
    #         frames_per_buffer=chunk,
    #     )

    #     frames = []

    #     data = stream.read(chunk)
    #     frames.append(data)

    #     stream.stop_stream()
    #     stream.close()
    #     p.terminate()

    #     audio_data = b"".join(frames)
    #     audio_io = io.BytesIO()
    #     wf = wave.open(audio_io, "wb")
    #     wf.setnchannels(channels)
    #     wf.setsampwidth(p.get_sample_size(format))
    #     wf.setframerate(rate)
    #     wf.writeframes(audio_data)
    #     wf.close()

    #     # Seek to the beginning of the BytesIO object before reading it for upload
    #     audio_io.seek(0)
    #     self.utils.upload_content_to_blob_storage(
    #         self.container_name_audio, self.blob_name_audio, audio_io
    #     )

    # def record_screen(self, duration, fps=15):
    #     sct = mss.mss()
    #     monitor = sct.monitors[1]

    #     fourcc = cv2.VideoWriter_fourcc(*"XVID")

    #     video_io = io.BytesIO()

    #     # Temporarily save to a local file (necessary for cv2.VideoWriter)
    #     temp_filename = "temp_video.avi"
    #     out = cv2.VideoWriter(
    #         temp_filename, fourcc, fps, (monitor["width"], monitor["height"])
    #     )

    #     start_time = time.time()
    #     while time.time() - start_time < duration:
    #         img = np.array(sct.grab(monitor))
    #         img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    #         out.write(img)

    #     out.release()

    #     self.utils.upload_file_to_blob_storage(
    #         self.container_name_video, temp_filename, self.blob_name_video
    #     )
    #     # Optionally, clean up the temporary file
    #     os.remove(temp_filename)

    # def start_recording(self, duration):
    #     # Start audio and screen recording in separate threads
    #     audio_thread = threading.Thread(target=self.record_audio, args=(duration,))
    #     screen_thread = threading.Thread(target=self.record_screen, args=(duration,))

    #     audio_thread.start()
    #     screen_thread.start()

    #     audio_thread.join()
    #     screen_thread.join()

    #     st.session_state["recording"] = False

    # def stop_recording():
    #     st.session_state["recording"] = False

    def go_to_course(self, course_name):
        """
        Callback function for the button that redirects to the course overview page.
        """
        st.session_state.selected_course = course_name
        st.session_state.selected_phase = "lectures"

    def run(self):
        self.db_dal.update_last_phase("record_lecture")
        st.title(
            # f"Leermateriaal genereren: College — {st.session_state.selected_module}"
            f"College {st.session_state.selected_module}"
        )
        st.write(
            "De opname van dit college is nog in afwachting. Wanneer dit gebeurd is, zal de content snel beschikbaar komen voor de kwaliteitscheck."
        )

        course_name = st.session_state.selected_course

        st.button(
            "Terug naar collegeoverzicht",
            key=course_name,
            on_click=self.go_to_course,
            args=(course_name,),
            use_container_width=True,
        )

    # -------------------------------------------------------------------------------------------
    # Uitgecommende code voor het genereren van leermateriaal
    # st.write(
    #     "Er is nog geen leermateriaal voor dit college gegenereerd. Kies een opname om de leermaterialen te genereren."
    # )

    # # user = st.session_state.username

    # # TODO - List actual recordings from blob storage for Demo
    # recordings_listing = [
    #     {
    #         "id": "1",
    #         "title": f"Moleculaire biologie 2023",
    #         "description": "Opgenomen op 16 oktober 2023 om 9:00",
    #     },
    #     {
    #         "id": "2",
    #         "title": f"Moleculaire biologie 2022",
    #         "description": "Opgenomen op 17 oktober 2022 om 9:00",
    #     },
    #     {
    #         "id": "3",
    #         "title": f"Moleculaire biologie 2021",
    #         "description": "Opgenomen op 18 oktober 2021 om 9:00",
    #     },
    # ]
    # for recording in recordings_listing:
    #     container = st.container(border=True)
    #     cols = container.columns([3, 1, 2])

    #     with cols[0]:
    #         st.subheader(recording["title"])
    #         st.write(recording["description"])

    #     with cols[1]:
    #         if recording["id"] == "1":
    #             st.image("src/data/images/recording_2023.png")
    #         else:
    #             st.image("src/data/images/icon_for_video.png")

    #     with cols[2]:
    #         with st.container():
    #             st.markdown(
    #                 "<div style='height: 20px;'></div>", unsafe_allow_html=True
    #             )  # Top padding
    #             st.button(
    #                 "Genereer leermateriaal",
    #                 key=recording["id"],
    #                 on_click=self.generate_materials,
    #                 use_container_width=True,
    #             )
    #             st.markdown(
    #                 "<div style='height: 20px;'></div>", unsafe_allow_html=True
    #             )  # Bottom padding
    #         # st.button(  # TODO: Invoke Cloud Function / API to generate practice materials
    #         #     "Genereer leertraject",
    #         #     key=recording["id"],
    #         #     on_click=self.generate_materials,
    #         #     use_container_width=True,
    #         # )

    # self.rerun_if_generated()

    # -------------------------------------------------------------------------------

    # def show_spinner_till_generated(self):
    #     with st.spinner("Oefenmaterialen worden gegenereerd..."):
    #         url = "https://contentpipeline.azurewebsites.net/api/contentpipeline?code=YxHEt2ZBmN6YX912nsC_i9KVpof7RVlr3k1yMSmZXlajAzFu_xvH1w=="
    #         params = {
    #             "lecture": "celbio_3",
    #             "run_full_pipeline": "true",
    #             "upload_to_demo_db": "true",
    #         }
    #         print(f"Sending http request to: {url} with params: {params}")
    #         # requests.get(url, params=params)
    #         while st.session_state.generated is False:
    #             status = self.db_dal.fetch_module_status()
    #             if status == "generated":
    #                 st.session_state.generated = True
    #             time.sleep(1)  # Sleep to avoid overwhelming the database with requests

    def generate_materials(self):
        st.title("Leermateriaal wordt gegenereerd")
        st.write("Even geduld alsjeblieft...")
        progress_bar = st.progress(0)
        for percent_complete in range(101):
            time.sleep(
                0.1
            )  # Simulates a time-consuming process (100 steps of 0.1 seconds each)
            progress_bar.progress(percent_complete)
        self.db_dal.update_module_status("generated")
        st.balloons()
        time.sleep(
            2
        )  # Wait for the balloons to finish before setting the session state
        st.session_state.generated = True

    def rerun_if_generated(self):
        # Rerun necessary to render the correct page, namely quality check
        if st.session_state.generated:
            st.session_state.generated = False
            st.session_state.selected_phase = "quality_check"
            st.rerun()


if __name__ == "__main__":
    Recorder("video", "video_output.avi", "audio", "audio_output.mp3").run()
