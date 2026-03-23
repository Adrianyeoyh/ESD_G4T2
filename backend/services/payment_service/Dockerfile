FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/payment_service /service

RUN pip install --no-cache-dir -r requirements/payment.txt

EXPOSE 5004

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5004"]