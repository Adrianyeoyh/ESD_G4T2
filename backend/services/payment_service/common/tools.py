# shared ENUMS / pre defined types or interfaces
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"