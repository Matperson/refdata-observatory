"""Tests de la validation des ISIN (spécification : docs/journal.md)."""

from dataclasses import dataclass

import pytest

from refdata.identifiers import (
    IsinFailure,
    IsinWarning,
    validate_isin,
)

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class Case:
    """Un cas de test : une entrée et le résultat attendu."""

    name: str
    raw: str
    valid: bool
    failures: frozenset[IsinFailure]
    warnings: frozenset[IsinWarning]
    normalized: str


CASES: tuple[Case, ...] = (
    Case(
        name="ISIN réel, US",
        raw="US0378331005",
        valid=True,
        failures=frozenset(),
        warnings=frozenset(),
        normalized="US0378331005",
    ),
    Case(
        name="minuscules",
        raw="us0378331005",
        valid=True,
        failures=frozenset(),
        warnings=frozenset({IsinWarning.CASE_CORRECTED}),
        normalized="US0378331005",
    ),
)
CASE_IDS = [case.name for case in CASES]


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_validation_matches_expected_result(case: Case) -> None:
    result = validate_isin(case.raw)
    assert result.valid == case.valid
    assert result.failures == case.failures
    assert result.warnings == case.warnings
    assert result.normalized == case.normalized
