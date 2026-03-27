from twilio.rest import Client
from app.config.settings import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
)

class TwilioService:
    def __init__(self):
        missing = [
            name for name, val in [
                ("TWILIO_ACCOUNT_SID", TWILIO_ACCOUNT_SID),
                ("TWILIO_AUTH_TOKEN", TWILIO_AUTH_TOKEN),
                ("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
            ] if not val
        ]
        if missing:
            raise ValueError(f"Missing required Twilio config: {', '.join(missing)}")

        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def send_sms(self, to_number: str, body: str) -> str:
        message = self.client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
        )
        return message.sid