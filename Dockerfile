# Use an official Python runtime as a parent image
FROM python:3.8

# Sets environment variable. Ensures that the python output is set straight to the terminal (unbuffered)
# and also that it’s in utf-8.
ENV PYTHONUNBUFFERED 1

# Set working directory in the container
WORKDIR /app

# Copy requirements file to the container
COPY requirements.txt .

# Install the requirements
RUN pip install -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Specify the command to run on container start
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]