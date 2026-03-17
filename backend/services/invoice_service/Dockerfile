FROM python:3.12-slim

WORKDIR /app

COPY shared /app/shared
COPY services/invoice_service /app/services/invoice_service

RUN pip install --no-cache-dir -r /app/services/invoice_service/requirements.txt

CMD ["python", "-m", "services.invoice_service.run"]