import enum


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    MODERATOR = "moderator"
    ADMINISTRATION = "administration"
    SOCIAL_SERVICE = "social_service"
    SERVICE_PROVIDER = "service_provider"
    SUPER_ADMIN = "super_admin"


OFFICIAL_ROLES = {
    UserRole.MODERATOR,
    UserRole.ADMINISTRATION,
    UserRole.SOCIAL_SERVICE,
}
