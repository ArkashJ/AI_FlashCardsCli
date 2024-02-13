# Dockerize python application

# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /flashcards

# Copy the current directory contents into the container at /app
COPY . /flashcards/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME Flashcards

# Run app.py when the container launches
CMD ["python", "flashcards.py"]
