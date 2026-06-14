#This will be the docker file for our main api, which will be used to serve our model and handle requests from the frontend.
# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /backend

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]