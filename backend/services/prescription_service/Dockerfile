FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/prescription_service /service

RUN pip install --no-cache-dir -r requirements/base.txt

EXPOSE 5005

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5005"]
