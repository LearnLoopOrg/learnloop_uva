FROM python:3.12-slim

WORKDIR /streamlit_app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure that the logs are printed while running in docker
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]