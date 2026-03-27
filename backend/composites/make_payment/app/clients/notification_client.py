import json

import pika

from app.config import settings


def publish_success_notification(record_id: int, invoice_id: int, payment_intent_id: str | None) -> None:
    body = {
        "phoneNumber": settings.NOTIFICATION_PHONE_NUMBER,
        "message": (
            f"Payment successful for record {record_id}, invoice {invoice_id}. "
            f"Ref: {payment_intent_id or 'n/a'}."
        ),
    }

    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=settings.RABBITMQ_QUEUE,
        body=json.dumps(body),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()
