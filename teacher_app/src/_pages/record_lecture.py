from utils.utils import *
import streamlit as st
import sounddevice as sd
import numpy as np
import cv2
import mss
import threading
import wave
import time
import pyaudio
import io
import os

load_dotenv()

class Recorder:
    def __init__(self):
        self.container_name_video = "video"
        self.blob_name_video = "video_output.avi"
        self.container_name_audio = "audio"
        self.blob_name_audio = "video_output.mp3"
        self.utils = Utils()

    def record_audio(self, duration):
        format = pyaudio.paInt16
        channels = 2
        rate = 44100
        chunk = duration * rate
        
        p = pyaudio.PyAudio()

        stream = p.open(format=format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)

        frames = []

        data = stream.read(chunk)
        frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_data = b''.join(frames)
        audio_io = io.BytesIO()
        wf = wave.open(audio_io, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(audio_data)
        wf.close()

        # Seek to the beginning of the BytesIO object before reading it for upload
        audio_io.seek(0)
        self.utils.upload_content_to_blob_storage( self.container_name_audio, self.blob_name_audio, audio_io )

    def record_screen(self, duration, fps=15):
        sct = mss.mss()
        monitor = sct.monitors[1]

        fourcc = cv2.VideoWriter_fourcc(*"XVID")

        video_io = io.BytesIO()
        
        # Temporarily save to a local file (necessary for cv2.VideoWriter)
        temp_filename = 'temp_video.avi'
        out = cv2.VideoWriter(temp_filename, fourcc, fps, (monitor["width"], monitor["height"]))

        start_time = time.time()
        while time.time() - start_time < duration:
            img = np.array(sct.grab(monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(img)

        out.release()

        self.utils.upload_file_to_blob_storage(self.container_name_video, temp_filename, self.blob_name_video)
        # Optionally, clean up the temporary file
        os.remove(temp_filename)
    
    def start_recording(self, duration):
        # Start audio and screen recording in separate threads
        audio_thread = threading.Thread(target=self.record_audio, args=( duration, ))
        screen_thread = threading.Thread(target=self.record_screen, args=( duration, ))
        
        audio_thread.start()
        screen_thread.start()

        audio_thread.join()
        screen_thread.join()
        
        st.session_state['recording'] = False

    def stop_recording():
        st.session_state['recording'] = False

    def run(self):
        st.title(f"Record lecture {st.session_state.selected_module}")
        st.write("This lecture hasn't been recorded yet. Click the button below to start recording.")

        if 'recording' not in st.session_state:
            st.session_state['recording'] = False

        duration_minutes = st.slider("Select duration (minutes)", min_value=1, max_value=120, value=60)
        duration_seconds = 60 * duration_minutes

        if st.button("Start recording"):
            st.session_state['recording'] = True
            self.start_recording(duration_seconds)


if __name__ == "__main__":
    Recorder("video", "video_output.avi", "audio", "audio_output.mp3" ).run()
