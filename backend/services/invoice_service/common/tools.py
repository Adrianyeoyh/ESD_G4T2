# shared ENUMS / pre defined types or interfaces
import enum

class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"