FROM python:3.12-slim 
WORKDIR /app
COPY requirements.txt .
# set the environment variable to avoid buffering issues
ENV PYTHONUNBUFFERED=1
#set non-root user
RUN useradd -m appuser
# change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app
# switch to the non-root user
USER appuser
# install dependencies
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
#Expose the port that the application will run on
EXPOSE 5000
# --config python:app  tells gunicorn to look for hook functions
# (post_fork, on_starting, etc.) in the app.py module itself
CMD ["python", "-m", "gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--config", "python:app", \
     "app:app"]
 