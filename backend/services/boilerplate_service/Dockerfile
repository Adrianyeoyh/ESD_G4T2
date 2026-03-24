FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY services/boilerplate_service /service

RUN pip install --no-cache-dir -r requirements/boilerplate.txt

EXPOSE 5100

CMD ["python", "run.py"]