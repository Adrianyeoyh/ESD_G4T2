FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/invoice_service /service

RUN pip install --no-cache-dir -r requirements/invoice.txt

EXPOSE 5000

CMD ["python", "run.py"]