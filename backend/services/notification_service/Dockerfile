FROM python:3.12-slim

WORKDIR /app

COPY requirements /service/requirements
COPY services/notification_service /service

RUN pip install --no-cache-dir -r requirements/notification.txt

CMD ["python", "app/run.py"]