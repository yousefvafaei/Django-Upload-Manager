# Use Python 3.9 as base image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the codebase
COPY . /code/

# Default command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
