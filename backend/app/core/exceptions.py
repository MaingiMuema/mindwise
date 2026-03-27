class ServiceConfigurationError(RuntimeError):
    """Raised when a required integration is unavailable or misconfigured."""


class ExternalServiceError(RuntimeError):
    """Raised when an upstream provider fails to complete a request."""
