FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY apps /app/apps
ENV PYTHONPATH=/app
CMD ["rq", "worker", "events"]
