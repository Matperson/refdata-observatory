"""Validation des identifiants ISIN (ISO 6166).

Spécification : docs/journal.md, entrée du 2026-11-27.
Aucune exception n'est levée pour une valeur invalide : le résultat la décrit.
"""

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "IsinFailure",
    "IsinValidation",
    "IsinWarning",
    "is_valid_isin",
    "validate_isin",
]


class IsinFailure(StrEnum):
    """Raisons pour lesquelles une valeur n'est pas un ISIN valide (valeurs stables)."""

    WRONG_LENGTH = "wrong_length"
    FORBIDDEN_CHARACTERS = "forbidden_characters"
    INVALID_PREFIX_FORMAT = "invalid_prefix_format"
    INVALID_CHECK_DIGIT = "invalid_check_digit"


class IsinWarning(StrEnum):
    """Écarts de forme corrigés pendant la validation (valeurs stables)."""

    CASE_CORRECTED = "case_corrected"
    WHITESPACE_REMOVED = "whitespace_removed"


@dataclass(frozen=True, slots=True)
class IsinValidation:
    """Résultat détaillé de la validation d'une valeur."""

    received: str
    normalized: str
    failures: frozenset[IsinFailure]
    warnings: frozenset[IsinWarning]

    @property
    def valid(self) -> bool:
        """Vrai si et seulement si aucune raison d'échec n'est présente."""
        raise NotImplementedError


def validate_isin(value: str) -> IsinValidation:
    """Normalise puis valide une valeur, et décrit le résultat."""
    raise NotImplementedError


def is_valid_isin(value: str) -> bool:
    """Raccourci : vrai si et seulement si ``validate_isin(value).valid``."""
    raise NotImplementedError
