from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(max_length=20)
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)
    model: str | None = None


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)
    model: str = "nano-banana"
    width: int = Field(default=1024, ge=256, le=1536)
    height: int = Field(default=1024, ge=256, le=1536)


class ChatResponse(BaseModel):
    reply: str
    remaining: int
    daily_limit: int
    limit_reached: bool = False
    payment_info: dict | None = None
    model: str | None = None


class ImageResponse(BaseModel):
    url: str | None = None
    model: str
    prompt: str
    provider: str | None = None
    error: str | None = None


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


class ModelsResponse(BaseModel):
    chat_models: list[dict]
    image_models: list[dict]
    capabilities: list[str]
    status: dict | None = None


class AIStatusResponse(BaseModel):
    ready: bool
    chat_provider: str
    image_provider: str
    pollinations_configured: bool
    openrouter_configured: bool = False
    openai_configured: bool = False
    perplexity_configured: bool = False
    gemini_configured: bool
    providers: list[str] = []
    message: str
    limits: dict | None = None
