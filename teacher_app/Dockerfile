FROM python:3.12-slim

WORKDIR /teacher_app

# Copy the requirements file first
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure that the logs are printed while running in docker
ENV PYTHONUNBUFFERED=1

EXPOSE 8502

CMD ["streamlit", "run", "src/main.py", "--server.port=8502"]