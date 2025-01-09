FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the environment file and requirements.txt from the root directory
COPY .env /app/.env
COPY service-account.json /app/service-account.json
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src directory into the container
# COPY src/ /app/src/

# Expose the port that the app runs on
EXPOSE 8000


