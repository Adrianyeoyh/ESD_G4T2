# shared ENUMS / pre defined types or interfaces
import enum

class InvoiceStatus(enum.Enum):
    UNPAID = "UNPAID"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"