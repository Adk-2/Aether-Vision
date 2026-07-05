"""Identity resolution exceptions."""


class IdentityError(Exception):
    """Base exception for identity resolution failures."""


class IdentityNotFoundError(IdentityError):
    """Raised when a requested track has no resolved identity."""
