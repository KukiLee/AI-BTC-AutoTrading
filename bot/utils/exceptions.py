"""Custom exceptions for controlled bot error handling."""


class BotError(Exception):
    """Base bot error."""


class ConfigurationError(BotError):
    """Raised when startup configuration is invalid."""


class DataValidationError(BotError):
    """Raised when expected data is missing or malformed."""


class ExchangeAdapterError(BotError):
    """Raised for exchange adapter failures."""


class RiskValidationError(BotError):
    """Raised when setup or size violates risk controls."""
