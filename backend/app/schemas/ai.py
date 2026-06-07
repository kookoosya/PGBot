from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    remaining: int
    daily_limit: int
    limit_reached: bool = False
    payment_info: dict | None = None


class UsageResponse(BaseModel):
    used: int
    remaining: int
    daily_limit: int
    payment_info: dict


class PaymentInfoResponse(BaseModel):
    card_number: str
    card_holder: str
    bank_name: str
    description: str
    amount_suggested: int
    contact_email: str
    message: str
