FROM python:3.12-slim
# set working directory
WORKDIR /app
# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# copy project
COPY . .
# expose port
EXPOSE 3000
# run the application
CMD ["python", "main.py"]
#don't run the development server in production
#use this command:
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]