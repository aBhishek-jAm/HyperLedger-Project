# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install the Python libraries your app uses
RUN pip install flask requests

# Copy all the files from your computer's aries_ui folder into the container
COPY . /app

# The command that starts your website when the container loads
CMD ["python", "app.py"]