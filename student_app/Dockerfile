FROM python:3.12-slim

<<<<<<< HEAD:streamlit_app/Dockerfile
WORKDIR /streamlit_app

COPY requirements.txt .
=======
WORKDIR /student_app
>>>>>>> aa500f2501614f7a1983acf74afbe956d41566b1:student_app/Dockerfile

# Copy the requirements file first

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Ensure that the logs are printed while running in docker
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py"]