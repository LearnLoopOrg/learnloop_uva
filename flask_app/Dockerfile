# Base image
FROM python:3.12-slim

WORKDIR /app

# Copy and cache dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of files to work directory
COPY . .

# Ensure that the logs are printed while running in docker
ENV PYTHONUNBUFFERED=1

# # Copy modified nginx configuration
COPY server.conf /etc/nginx/conf.d/server.conf

# Use 4 workers for gunicorn and make the app accessible from outside the container with 0.0.0.0:3000
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:3000", "main:app"]

# Set port used by container
EXPOSE 3000
