"""
Custom exceptions for multi-platform chess analysis.

Provides a hierarchy of exceptions for different error categories,
enabling precise error handling throughout the application.
"""

from typing import Optional, Any


class ChessAnalysisError(Exception):
    """
    Base exception for all chess analysis errors.

    All custom exceptions inherit from this, making it easy to catch
    any chess analysis related error.
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# =============================================================================
# Platform Errors
# =============================================================================


class PlatformError(ChessAnalysisError):
    """Base exception for platform-related errors."""

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.platform = platform


class APIError(PlatformError):
    """
    Error communicating with a platform's API.

    Includes HTTP status code and response details when available.
    """

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        url: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, platform, details)
        self.status_code = status_code
        self.response_body = response_body
        self.url = url

    def __str__(self) -> str:
        parts = [self.message]
        if self.platform:
            parts.append(f"Platform: {self.platform}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.url:
            parts.append(f"URL: {self.url}")
        return " | ".join(parts)


class RateLimitError(APIError):
    """
    Rate limit exceeded on a platform API.

    Includes retry information when available.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        platform: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, platform, status_code=429, details=details)
        self.retry_after = retry_after  # Seconds to wait before retry

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} | Retry after: {self.retry_after}s"
        return base


class AuthenticationError(PlatformError):
    """
    Authentication failed for a platform API.

    Raised when API tokens are invalid, expired, or missing.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        platform: Optional[str] = None,
        requires_token: bool = True,
        details: Optional[dict] = None,
    ):
        super().__init__(message, platform, details)
        self.requires_token = requires_token


class UserNotFoundError(PlatformError):
    """
    User/player not found on a platform.
    """

    def __init__(
        self,
        username: str,
        platform: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        message = f"User '{username}' not found"
        if platform:
            message += f" on {platform}"
        super().__init__(message, platform, details)
        self.username = username


class PlatformNotSupportedError(PlatformError):
    """
    Requested platform is not supported.
    """

    def __init__(
        self,
        platform: str,
        supported_platforms: Optional[list] = None,
        details: Optional[dict] = None,
    ):
        message = f"Platform '{platform}' is not supported"
        if supported_platforms:
            message += f". Supported: {', '.join(supported_platforms)}"
        super().__init__(message, platform, details)
        self.supported_platforms = supported_platforms or []


# =============================================================================
# Data Normalization Errors
# =============================================================================


class NormalizationError(ChessAnalysisError):
    """
    Error normalizing platform data to common schema.

    Raised when platform-specific data cannot be converted to
    the normalized format.
    """

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        field: Optional[str] = None,
        raw_value: Any = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.platform = platform
        self.field = field
        self.raw_value = raw_value

    def __str__(self) -> str:
        parts = [self.message]
        if self.platform:
            parts.append(f"Platform: {self.platform}")
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.raw_value is not None:
            parts.append(f"Value: {self.raw_value!r}")
        return " | ".join(parts)


class InvalidPGNError(NormalizationError):
    """
    Invalid or unparseable PGN data.
    """

    def __init__(
        self,
        message: str = "Invalid PGN data",
        pgn_snippet: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, field="pgn", details=details)
        self.pgn_snippet = pgn_snippet


class MissingDataError(NormalizationError):
    """
    Required data is missing from the platform response.
    """

    def __init__(
        self,
        field: str,
        platform: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        message = f"Required field '{field}' is missing"
        super().__init__(message, platform=platform, field=field, details=details)


# =============================================================================
# Analysis Errors
# =============================================================================


class AnalysisError(ChessAnalysisError):
    """Base exception for analysis-related errors."""

    def __init__(
        self,
        message: str,
        analyzer_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.analyzer_id = analyzer_id


class InsufficientDataError(AnalysisError):
    """
    Not enough data to perform meaningful analysis.
    """

    def __init__(
        self,
        message: str = "Insufficient data for analysis",
        required_games: Optional[int] = None,
        available_games: Optional[int] = None,
        analyzer_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, analyzer_id, details)
        self.required_games = required_games
        self.available_games = available_games

    def __str__(self) -> str:
        base = super().__str__()
        if self.required_games and self.available_games is not None:
            return f"{base} | Required: {self.required_games}, Available: {self.available_games}"
        return base


class EngineError(AnalysisError):
    """
    Error with chess engine (e.g., Stockfish).
    """

    def __init__(
        self,
        message: str,
        engine_name: Optional[str] = None,
        engine_path: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, analyzer_id="engine", details=details)
        self.engine_name = engine_name
        self.engine_path = engine_path


class EngineNotFoundError(EngineError):
    """
    Chess engine executable not found.
    """

    def __init__(
        self,
        engine_path: str,
        engine_name: str = "Stockfish",
        details: Optional[dict] = None,
    ):
        message = f"{engine_name} not found at '{engine_path}'"
        super().__init__(message, engine_name, engine_path, details)


# =============================================================================
# LLM Errors
# =============================================================================


class LLMError(ChessAnalysisError):
    """Base exception for LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.provider = provider
        self.model = model


class LLMProviderError(LLMError):
    """
    Error with LLM provider configuration or availability.
    """

    def __init__(
        self,
        message: str,
        provider: str,
        details: Optional[dict] = None,
    ):
        super().__init__(message, provider=provider, details=details)


class LLMAPIError(LLMError):
    """
    Error calling LLM API.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, provider, model, details)
        self.status_code = status_code


class LLMRateLimitError(LLMAPIError):
    """
    LLM API rate limit exceeded.
    """

    def __init__(
        self,
        provider: str,
        model: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        message = f"Rate limit exceeded for {provider}"
        if model:
            message += f" ({model})"
        super().__init__(message, provider, model, status_code=429, details=details)
        self.retry_after = retry_after


class ModelNotSupportedError(LLMError):
    """
    Requested LLM model is not supported.
    """

    def __init__(
        self,
        model: str,
        provider: Optional[str] = None,
        supported_models: Optional[list] = None,
        details: Optional[dict] = None,
    ):
        message = f"Model '{model}' is not supported"
        if provider:
            message += f" by {provider}"
        if supported_models:
            message += f". Supported: {', '.join(supported_models)}"
        super().__init__(message, provider, model, details)
        self.supported_models = supported_models or []


# =============================================================================
# Report Errors
# =============================================================================


class ReportError(ChessAnalysisError):
    """Base exception for report generation errors."""

    def __init__(
        self,
        message: str,
        report_type: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.report_type = report_type


class ReportGenerationError(ReportError):
    """
    Error generating a report.
    """

    pass


class InvalidReportConfigError(ReportError):
    """
    Invalid report configuration.
    """

    def __init__(
        self,
        message: str,
        invalid_fields: Optional[list] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details=details)
        self.invalid_fields = invalid_fields or []


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(ChessAnalysisError):
    """
    Error in application configuration.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.config_key = config_key


class MissingConfigError(ConfigurationError):
    """
    Required configuration is missing.
    """

    def __init__(
        self,
        config_key: str,
        env_var: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        message = f"Missing required configuration: {config_key}"
        if env_var:
            message += f" (set {env_var} environment variable)"
        super().__init__(message, config_key, details)
        self.env_var = env_var
