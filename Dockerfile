# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

RUN apt-get update && apt-get install -y postgresql-client
# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /code/

# Collect static files (if using Django staticfiles)
RUN python manage.py collectstatic --noinput || true

# Expose port (change if needed)
EXPOSE 8000

# Start server (change if using gunicorn/uwsgi in prod)
CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
