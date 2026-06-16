from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_VK_FRAME_ANCESTORS = (
    "frame-ancestors 'self' https://vk.com https://*.vk.com https://vk.ru https://*.vk.ru;"
)
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
_VK_MINI_CSP = _DEFAULT_CSP.replace("frame-ancestors 'none';", _VK_FRAME_ANCESTORS)


def _is_vk_mini_app_path(path: str) -> bool:
    return path == "/vk" or path.startswith("/vk/")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        vk_mini = _is_vk_mini_app_path(request.url.path)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if vk_mini:
            response.headers.pop("X-Frame-Options", None)
        else:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = _VK_MINI_CSP if vk_mini else _DEFAULT_CSP
        if request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response
