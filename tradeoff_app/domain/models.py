"""Domain models for the trade-off application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


Record = dict[str, Any]


@dataclass(frozen=True)
class Alternative:
    """Option under comparison."""

    id: str
    name: str
    description: str


@dataclass(frozen=True)
class Attribute:
    """Qualitative attribute scored for each alternative."""

    id: str
    name: str
    description: str


@dataclass(frozen=True)
class Scenario:
    """Decision scenario used in the aggregate analysis."""

    id: str
    name: str
    description: str
    weight: float


@dataclass(frozen=True)
class Profile:
    """Analysis profile that defines one consistent set of weights and scores."""

    id: str
    name: str
    description: str


@dataclass(frozen=True)
class WeightEntry:
    """Profile and scenario specific weight configuration for one attribute."""

    profile_id: str
    scenario_id: str
    attribute_id: str
    global_weight: float
    local_weight: float


@dataclass(frozen=True)
class ScoreEntry:
    """Score assigned to one alternative/scenario/profile tuple."""

    profile_id: str
    scenario_id: str
    alternative_id: str
    score: float


@dataclass(frozen=True)
class Formula:
    """User-defined or built-in metric expression stored as LaTeX-like input."""

    id: str
    name: str
    latex: str
    description: str
    builtin: bool = False
    enabled: bool = True


def alternative_from_record(record: Record) -> Alternative:
    return Alternative(
        id=str(record["id"]),
        name=str(record["name"]),
        description=str(record.get("description", "")),
    )


def attribute_from_record(record: Record) -> Attribute:
    return Attribute(
        id=str(record["id"]),
        name=str(record["name"]),
        description=str(record.get("description", "")),
    )


def scenario_from_record(record: Record) -> Scenario:
    return Scenario(
        id=str(record["id"]),
        name=str(record["name"]),
        description=str(record.get("description", "")),
        weight=float(record.get("weight", 0.0)),
    )


def profile_from_record(record: Record) -> Profile:
    return Profile(
        id=str(record["id"]),
        name=str(record["name"]),
        description=str(record.get("description", "")),
    )


def weight_entry_from_record(record: Record) -> WeightEntry:
    return WeightEntry(
        profile_id=str(record.get("profile_id", "")),
        scenario_id=str(record["scenario_id"]),
        attribute_id=str(record["attribute_id"]),
        global_weight=float(record.get("global_weight", 0.0)),
        local_weight=float(record.get("local_weight", 0.0)),
    )


def score_from_record(record: Record) -> ScoreEntry:
    return ScoreEntry(
        profile_id=str(record.get("profile_id", "")),
        scenario_id=str(record["scenario_id"]),
        alternative_id=str(record["alternative_id"]),
        score=float(record.get("score", 0.0)),
    )


def formula_from_record(record: Record) -> Formula:
    return Formula(
        id=str(record["id"]),
        name=str(record["name"]),
        latex=str(record.get("latex", "")),
        description=str(record.get("description", "")),
        builtin=bool(record.get("builtin", False)),
        enabled=bool(record.get("enabled", True)),
    )
