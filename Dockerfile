# Use an official Python runtime as a parent image
FROM python:3.5-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/
COPY optional-requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install Django==1.11.17
RUN pip install -r requirements.txt
RUN pip install -r optional-requirements.txt

# Copy the entire Django project directory into the container at /app
COPY . /app/
