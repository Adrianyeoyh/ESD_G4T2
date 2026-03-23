FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/invoice_service /service

RUN pip install --no-cache-dir -r requirements/invoice.txt

EXPOSE 5003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5003"]