FROM python:3.12-slim

WORKDIR /teacher_app

# Copy the requirements file first
COPY . .

# Install build dependencies for pyaudio package
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     portaudio19-dev \
#     python3-dev \
#     libgl1-mesa-glx \
#     libglib2.0-0 \
#     libsm6 \
#     libxext6 \
#     libxrender-dev \
#     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure that the logs are printed while running in docker
ENV PYTHONUNBUFFERED=1

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "src/main.py", "--server.port=8502", "--server.address=0.0.0.0"]