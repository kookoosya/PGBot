"""Verification API response mapping."""

from app.models.user import User
from app.schemas.verification import VerificationRequestResponse


def verification_to_response(user: User) -> VerificationRequestResponse:
    """Map a pending user to verification API response."""
    return VerificationRequestResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        organization=user.organization,
        position=user.position,
        role=user.role.name,
        verification_status=user.verification_status,
        verification_note=user.verification_note,
        created_at=user.created_at,
    )
