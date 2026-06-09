from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(max_length=20)
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)
    model: str | None = None
    chat_mode: str = Field(default="chat", max_length=20)


class AIPlanResponse(BaseModel):
    id: str
    name: str
    daily_limit: int
    price_rub: int
    period_days: int
    tagline: str
    features: list[str]
    chat_modes: list[str]
    model_id: str
    requires_login: bool
    requires_payment: bool


class AIPlansResponse(BaseModel):
    plans: list[AIPlanResponse]
    notice: str


class AIAccessResponse(BaseModel):
    plan_id: str
    plan_name: str
    daily_limit: int
    chat_modes: list[str]
    model_id: str
    is_paid: bool
    expires_at: str | None = None
    payment_reference: str | None = None
    used: int
    remaining: int


class AIEntitlementGrantRequest(BaseModel):
    plan_id: str = Field(default="pro", max_length=32)
    user_id: int | None = None
    vk_id: int | None = None
    web_identifier: str | None = Field(default=None, max_length=255)
    period_days: int | None = Field(default=None, ge=1, le=365)
    payment_reference: str | None = Field(default=None, max_length=120)
    payment_amount: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class AIProviderKeyCreateRequest(BaseModel):
    api_key: str = Field(min_length=20, max_length=512)
    label: str | None = Field(default=None, max_length=120)
    priority: int = Field(default=100, ge=1, le=1000)


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
    plan_id: str | None = None
    plan_name: str | None = None
    is_paid: bool = False


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
    phone: str = ""
    card_holder: str
    bank_name: str
    description: str
    amount_suggested: int
    contact_email: str
    message: str
    auto_payment_available: bool = False
    bank_auto_available: bool = False
    bank_transfer_available: bool = False


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


class AISubscribeRequest(BaseModel):
    plan_id: str = Field(max_length=32)


class AISubscribeResponse(BaseModel):
    order_id: int
    payment_url: str
    amount_rub: int
    plan_id: str
    plan_name: str


class AIPaymentStatusResponse(BaseModel):
    order_id: int
    status: str
    plan_id: str
    entitlement_id: int | None = None
    activated: bool = False
    payment_code: str | None = None
    amount_rub: int | None = None


class BankPaymentResponse(BaseModel):
    order_id: int
    plan_id: str
    amount_rub: int
    payment_code: str
    status: str
    card_number: str
    phone: str
    card_holder: str
    bank_name: str
    comment: str
    instructions: str
    auto_enabled: bool = False
    activated: bool = False
