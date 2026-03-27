import json
import logging
import re
import signal
import time

import pika

from app.config.settings import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASS,
    RABBITMQ_QUEUE,
)
from app.services.twilio_service import TwilioService

logger = logging.getLogger(__name__)


class NotificationConsumer:
    MAX_RETRIES = 3
    MAX_RECONNECT_DELAY = 30

    def __init__(self):
        self.connection = None
        self.channel = None
        self.twilio_service = TwilioService()
        self._shutdown_requested = False

    def _connect(self):
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        self.channel.basic_qos(prefetch_count=1)
        logger.info("Connected to RabbitMQ at %s:%s", RABBITMQ_HOST, RABBITMQ_PORT)

    @staticmethod
    def _is_valid_phone(phone_number: str) -> bool:
        return bool(re.fullmatch(r"\+[1-9]\d{1,14}", phone_number))

    def callback(self, ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))

            phone_number = payload["phoneNumber"]
            message_body = payload["message"]

            if not isinstance(phone_number, str) or not self._is_valid_phone(phone_number):
                raise ValueError(f"Invalid phoneNumber format: {phone_number}")

            if not isinstance(message_body, str) or not message_body.strip():
                raise ValueError("message must be a non-empty string")

            twilio_sid = self.twilio_service.send_sms(
                to_number=phone_number,
                body=message_body,
            )

            logger.info("SMS sent successfully. Twilio SID: %s", twilio_sid)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Poison message — bad payload that will never succeed. Ack to drop.
            logger.warning("Dropping non-retryable message: %s", e)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # Retryable error (network, Twilio transient failure, etc.)
            headers = dict(getattr(properties, "headers", None) or {})
            retry_count = int(headers.get("x-retry-count", 0))

            if retry_count < self.MAX_RETRIES:
                headers["x-retry-count"] = retry_count + 1
                ch.basic_publish(
                    exchange="",
                    routing_key=RABBITMQ_QUEUE,
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type="application/json",
                        headers=headers,
                    ),
                )
                logger.warning(
                    "Retrying notification (%d/%d) after failure: %s",
                    retry_count + 1, self.MAX_RETRIES, e,
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error("Dropping notification after %d retries: %s", self.MAX_RETRIES, e)
                ch.basic_ack(delivery_tag=method.delivery_tag)

    def _shutdown(self, signum, _frame):
        logger.info("Received signal %s, shutting down gracefully...", signum)
        self._shutdown_requested = True
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()

    def start(self):
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

        reconnect_delay = 1
        while not self._shutdown_requested:
            try:
                self._connect()
                reconnect_delay = 1

                self.channel.basic_consume(
                    queue=RABBITMQ_QUEUE,
                    on_message_callback=self.callback,
                )
                logger.info("Waiting for messages on queue: %s", RABBITMQ_QUEUE)
                self.channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                if self._shutdown_requested:
                    break
                logger.error("RabbitMQ connection lost: %s. Reconnecting in %ds...", e, reconnect_delay)
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.MAX_RECONNECT_DELAY)

            except Exception as e:
                if self._shutdown_requested:
                    break
                logger.exception("Unexpected error: %s. Reconnecting in %ds...", e, reconnect_delay)
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.MAX_RECONNECT_DELAY)

            finally:
                if self.connection and self.connection.is_open:
                    try:
                        self.connection.close()
                    except Exception:
                        pass

        logger.info("Consumer shut down.")
