# Use the official Python image
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apk update \
    && apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the application code
COPY . .

# Create a directory for media files
RUN mkdir -p /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Apply Django migrations
RUN python manage.py migrate

# Expose the port that Daphne will run on
EXPOSE 3003

# Start the application using Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "3003", "paAI.wsgi:application"] 