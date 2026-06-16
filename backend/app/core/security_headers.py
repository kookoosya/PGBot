from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_VK_FRAME_ANCESTORS = "https://vk.com https://*.vk.com https://m.vk.com"

_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self' data:; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "upgrade-insecure-requests"
)

_VK_EMBED_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self' data:; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https:; "
    f"frame-ancestors {_VK_FRAME_ANCESTORS}; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def _allows_vk_embed(request: Request) -> bool:
    path = request.url.path
    if path.startswith("/vk") or path.startswith("/api/v1/vk/auth"):
        return True
    referer = request.headers.get("referer", "")
    return "vk.com" in referer


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        vk_embed = _allows_vk_embed(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        if not vk_embed:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = _VK_EMBED_CSP if vk_embed else _DEFAULT_CSP
        if request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response
