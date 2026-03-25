FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY composites/make_payment /service

RUN pip install --no-cache-dir -r requirements/boilerplate.txt

EXPOSE 5005

CMD ["python", "run.py"]
