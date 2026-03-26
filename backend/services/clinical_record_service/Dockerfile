FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/clinical_record_service /service

RUN pip install --no-cache-dir -r requirements/record.txt

EXPOSE 5006

CMD ["python", "run.py"]