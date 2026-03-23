FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/drug_catalogue_service /service

# Install the dependencies
RUN pip install --no-cache-dir -r requirements/drug_catalogue.txt

EXPOSE 5001

CMD ["python", "run.py"]