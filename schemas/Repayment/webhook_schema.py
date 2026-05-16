from pydantic import BaseModel
from typing import Optional, Literal, Union


# =====================================================
# COMMON ENTITY
# =====================================================
class BasePaymentEntity(BaseModel):
    id: str
    amount: int
    method: str
    status: Optional[str] = "captured"


# =====================================================
# UPI / CARD / NETBANKING
# =====================================================
class OnlinePaymentEntity(BasePaymentEntity):
    order_id: Optional[str] = None

# =====================================================
# BANK TRANSFER
# =====================================================
class BankTransferEntity(BasePaymentEntity):
    pass


# =====================================================
# WRAPPERS
# =====================================================
class OnlinePaymentWrapper(BaseModel):
    entity: OnlinePaymentEntity


class BankTransferWrapper(BaseModel):
    entity: BankTransferEntity


class OnlinePayload(BaseModel):
    payment: OnlinePaymentWrapper


class BankTransferPayload(BaseModel):
    payment: BankTransferWrapper


# =====================================================
# ONLINE EVENTS
# =====================================================
class OnlineWebhookSchema(BaseModel):
    event: Literal[
        "payment.captured",
        "payment.failed"
    ]

    payload: OnlinePayload

# =====================================================
# BANK TRANSFER EVENTS
# =====================================================
class BankTransferWebhookSchema(BaseModel):
    event: Literal[
        "payment.captured",
        "payment.failed"
    ]

    payload: BankTransferPayload


# =====================================================
# FINAL UNION
# =====================================================
WebhookSchema = Union[
    OnlineWebhookSchema,
    BankTransferWebhookSchema
]