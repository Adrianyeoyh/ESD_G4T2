FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/payment_service /service

RUN pip install --no-cache-dir -r requirements/payment.txt

EXPOSE 5000

CMD ["python", "run.py"]