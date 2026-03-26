FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY composites/prescribe_medicine /service

RUN pip install --no-cache-dir -r requirements/prescribe_medicine.txt

EXPOSE 5007

CMD ["python", "run.py"]