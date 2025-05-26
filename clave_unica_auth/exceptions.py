"""
Custom exceptions for the clave_unica_auth application.

These exceptions provide more specific error information for authentication
and API interaction failures related to ClaveUnica.
"""
class ClaveUnicaAuthError(Exception):
    """Base class for exceptions in this module."""
    pass

class InvalidStateError(ClaveUnicaAuthError):
    """Raised when the OAuth state is invalid or expired."""
    pass

class TokenExchangeError(ClaveUnicaAuthError):
    """Raised when exchanging an authorization code for an access token fails."""
    pass

class UserInfoError(ClaveUnicaAuthError):
    """Raised when fetching user information from ClaveUnica fails."""
    pass

class UserNotRegisteredError(ClaveUnicaAuthError):
    """Raised when a user is not found and auto-creation is disabled."""
    pass

class ClaveUnicaAPIError(ClaveUnicaAuthError):
    """Raised when the ClaveUnica API returns an error or is unreachable."""
    pass
