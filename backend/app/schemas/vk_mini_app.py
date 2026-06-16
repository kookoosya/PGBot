from pydantic import BaseModel, Field


class VkMiniAppAuthRequest(BaseModel):
    launch_params: str = Field(..., min_length=3, max_length=4096)


class VkMiniAppAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
