from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AtomicPaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(min_length=1)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AtomicPaymentResponse(BaseModel):
    status: str
    transaction_id: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
