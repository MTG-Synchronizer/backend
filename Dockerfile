FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy files from the root directory to the working directory
COPY .env /app/.env
COPY service-account.json /app/service-account.json
COPY requirements.txt /app/requirements.txt
COPY src/ /app/src/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app runs on
EXPOSE 8000


