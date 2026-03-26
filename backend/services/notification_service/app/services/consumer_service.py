import json
import pika

from app.config.settings import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASS,
    RABBITMQ_QUEUE,
)
from app.services.twilio_service import TwilioService


class NotificationConsumer:
    def __init__(self):
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

        # One message at a time per worker
        self.channel.basic_qos(prefetch_count=1)

        self.twilio_service = TwilioService()

    def callback(self, ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))

            phone_number = payload["phoneNumber"]
            message_body = payload["message"]

            twilio_sid = self.twilio_service.send_sms(
                to_number=phone_number,
                body=message_body,
            )

            print(f"SMS sent successfully. Twilio SID: {twilio_sid}")

            # Ack only after Twilio succeeds
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Failed to process notification: {e}")

            # Reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self):
        self.channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=self.callback,
        )
        print(f"Waiting for messages on queue: {RABBITMQ_QUEUE}")
        self.channel.start_consuming()