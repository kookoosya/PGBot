from pydantic import BaseModel, Field

from app.schemas.auth import Token, UserResponse


class VkSilentAuthRequest(BaseModel):
    silent_token: str = Field(min_length=1, max_length=2048)
    uuid: str = Field(min_length=1, max_length=128)


class VkAuthResponse(Token):
    user: UserResponse
