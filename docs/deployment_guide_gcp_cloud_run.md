# Deployment Guide: SAFA Global on Google Cloud Run

**Version**: 1.0  
**Last Updated**: July 27, 2024

This guide provides step-by-step instructions for deploying the SAFA Global Django project to Google Cloud Run, a scalable and cost-effective hosting solution. This allows testers and stakeholders to access the application via a public URL without accessing the source code.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup on Google Cloud](#project-setup-on-google-cloud)
3. [Prepare Your Django Application](#prepare-your-django-application)
4. [Containerize the Application (Dockerfile)](#containerize-the-application-dockerfile)
5. [Set Up the Database (Cloud SQL)](#set-up-the-database-cloud-sql)
6. [Manage Secrets](#manage-secrets)
7. [Build and Deploy](#build-and-deploy)
8. [Accessing the Deployed App](#accessing-the-deployed-app)

---

## 1. Prerequisites

- A Google Cloud Platform (GCP) account with billing enabled.
- The `gcloud` command-line tool installed and authenticated: Install gcloud CLI
- Docker installed on your local machine: Install Docker

---

## 2. Project Setup on Google Cloud

First, set up your project and enable the necessary APIs.

```bash
# 1. Set your project ID (replace 'your-gcp-project-id')
gcloud config set project your-gcp-project-id

# 2. Enable the necessary APIs for the project
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com
```

---

## 3. Prepare Your Django Application

Your application code is already well-structured for this. Ensure you have the following:

- **`requirements.txt`**: A file listing all Python dependencies. Make sure it includes `gunicorn` and `psycopg2-binary`.
- **Production Settings**: Your `settings.py` should be configured to read sensitive values (like `SECRET_KEY`, `DATABASE_URL`, `DEBUG`) from environment variables, which we will manage with Secret Manager. The `DEPLOYMENT_AND_AI_SERVICES_GUIDE.md` has a good list of variables to use.

---

## 4. Containerize the Application (Dockerfile)

A `Dockerfile` tells Cloud Build how to package your application into a container image. Create this file in the root of your `safa_global` project.

**`c:\Users\User\Documents\safa_global\Dockerfile`**:
```dockerfile
# Use the official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Collect static files (if you are serving them with whitenoise)
# This assumes you have configured whitenoise for static file serving in production
RUN python manage.py collectstatic --noinput

# Expose the port Gunicorn will run on
EXPOSE 8080

# Run the application using Gunicorn
# The "start.sh" script will be a simple wrapper to run migrations and start gunicorn
CMD ["gunicorn", "safa_global.wsgi:application", "--bind", "0.0.0.0:8080"]
```

---

## 5. Set Up the Database (Cloud SQL)

Create a managed PostgreSQL database.

```bash
# 1. Choose a name and region for your database instance
INSTANCE_NAME="safa-global-db"
REGION="europe-west1"

# 2. Create the PostgreSQL instance
gcloud sql instances create $INSTANCE_NAME --database-version=POSTGRES_13 --region=$REGION --cpu=1 --memory=4GB

# 3. Create the database within the instance
gcloud sql databases create safa_global_prod --instance=$INSTANCE_NAME

# 4. Create a database user
gcloud sql users create safa_user --instance=$INSTANCE_NAME --password="CHOOSE_A_STRONG_PASSWORD"
```

You will get a **Connection Name** for your instance (e.g., `your-gcp-project-id:europe-west1:safa-global-db`). You will need this later.

---

## 6. Manage Secrets

Store your Django `SECRET_KEY` and other sensitive data in Google Secret Manager.

```bash
# Store your Django secret key
echo -n "your-super-secret-django-key" | gcloud secrets create DJANGO_SECRET_KEY --data-file=-

# Store your database URL
# The format is important for Django to connect to Cloud SQL from Cloud Run
# postgresql://DB_USER:DB_PASSWORD@/DB_NAME?host=/cloudsql/INSTANCE_CONNECTION_NAME
DB_URL="postgresql://safa_user:CHOOSE_A_STRONG_PASSWORD@/safa_global_prod?host=/cloudsql/your-gcp-project-id:europe-west1:safa-global-db"
echo -n $DB_URL | gcloud secrets create DATABASE_URL --data-file=-
```

---

## 7. Build and Deploy

Now, use a single command to build the container image and deploy it to Cloud Run.

```bash
# Replace 'safa-global-app' with your desired service name
SERVICE_NAME="safa-global-app"

# Build and deploy
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --add-cloudsql-instances "your-gcp-project-id:europe-west1:safa-global-db" \
    --update-secrets=DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,DEBUG=False,ALLOWED_HOSTS="*" \
    --allow-unauthenticated
```

This command will:
1.  Upload your code to Google Cloud.
2.  Build the Docker image using Cloud Build.
3.  Push the image to Artifact Registry.
4.  Deploy the image to Cloud Run.
5.  Connect the service to your Cloud SQL database.
6.  Inject your secrets as environment variables.
7.  Make the service publicly accessible (`--allow-unauthenticated`).

The first deployment may take a few minutes. Subsequent deployments will be much faster.

---

## 8. Accessing the Deployed App

After the deployment command finishes, `gcloud` will provide you with a **Service URL** (e.g., `https://safa-global-app-xxxxxxxx-ew.a.run.app`).

You can share this URL with your testers. They can access the live application in their browser, log in, and test its functionality, all without ever seeing your code.