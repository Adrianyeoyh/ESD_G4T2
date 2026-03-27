import json
import logging

import pika

from app.config import settings

logger = logging.getLogger(__name__)

_connection: pika.BlockingConnection | None = None
_channel: pika.channel.Channel | None = None


def _get_channel() -> pika.channel.Channel:
    global _connection, _channel

    if _connection and _connection.is_open and _channel and _channel.is_open:
        return _channel

    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
    _connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
        )
    )
    _channel = _connection.channel()
    _channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
    return _channel


def publish_success_notification(
    record_id: int,
    invoice_id: int,
    payment_intent_id: str | None,
    phone_number: str,
) -> None:
    body = {
        "phoneNumber": phone_number,
        "message": (
            f"Payment successful for record {record_id}, invoice {invoice_id}. "
            f"Ref: {payment_intent_id or 'n/a'}."
        ),
    }

    try:
        channel = _get_channel()
        channel.basic_publish(
            exchange="",
            routing_key=settings.RABBITMQ_QUEUE,
            body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    except pika.exceptions.AMQPError:
        # Connection went stale — reset and retry once
        global _connection, _channel
        _connection = None
        _channel = None
        channel = _get_channel()
        channel.basic_publish(
            exchange="",
            routing_key=settings.RABBITMQ_QUEUE,
            body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2),
        )
