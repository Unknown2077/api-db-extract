class ExtractError(Exception):
    """Base for source extraction errors."""


class ConnectorError(ExtractError):
    """Network or protocol failure on source API."""


class ConfigError(ExtractError):
    """Missing or invalid environment configuration."""


class MapperError(ExtractError):
    """Raw record cannot be mapped to canonical format."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        super().__init__(f"Mapping failed on '{field}': {reason}")


class LoadError(Exception):
    """Base for target load errors."""


class TargetAPIError(LoadError):
    """Non-retryable 4xx from target API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Target API {status_code}: {message}")
