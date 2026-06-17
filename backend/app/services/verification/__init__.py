"""User verification — organization/official registration and approval."""

from .moderation import approve_verification, list_pending_verifications, reject_verification
from .register import register_official, register_organization
from .responses import verification_to_response
from .schemas import VerificationNotFoundError, VerificationValidationError

__all__ = [
    "VerificationNotFoundError",
    "VerificationValidationError",
    "approve_verification",
    "list_pending_verifications",
    "register_official",
    "register_organization",
    "reject_verification",
    "verification_to_response",
]
