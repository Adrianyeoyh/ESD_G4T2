FROM python:3.12-slim

WORKDIR /service

COPY requirements /service/requirements
COPY composites/make_payment /service

RUN pip install --no-cache-dir -r requirements/make_payment.txt

EXPOSE 5008

CMD ["python", "run.py"]
