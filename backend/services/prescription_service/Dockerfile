FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/prescription_service /service

# Install the dependencies
RUN pip install --no-cache-dir -r requirements/prescription.txt

EXPOSE 5005

CMD ["python", "run.py"]