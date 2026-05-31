FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
ENV PYTHONUNBUFFERED=1
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
CMD ["python", "worker.py"]