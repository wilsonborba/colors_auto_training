from typing import Any, Optional

from fastapi import status
from pydantic import BaseModel


class MalwareDetectedError(Exception):
    """Custom exception for malware detection."""

    pass


class UnsupportedFileTypeError(Exception):
    """Custom exception for unsupported file types."""

    pass


class DocumentNotFoundError(Exception):
    """Custom exception for document not found in cache."""

    pass


class InvalidTotalPagesError(Exception):
    """Custom exception for invalid total pages in cached document."""

    pass


class AIGenerationError(Exception):
    """Custom exception for AI generation errors."""

    pass


class NotEnoughQuestionsGeneratedError(Exception):
    """Custom exception when not enough questions are generated."""

    pass


class NoDefaultAIClientError(Exception):
    """Custom exception when no default AI client is set for the user."""

    pass
