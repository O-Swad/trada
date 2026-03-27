"""Reflex entry point for the Trade-Off Workbench."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any
from uuid import uuid4

import reflex as rx

from tradeoff_app.components.common import (
    FONT_BODY,
    FONT_DISPLAY,
    SERIES_COLORS,
    SURFACE,
    TEXT_MUTED,
    TEXT_STRONG,
    empty_state,
    panel,
    record_select,
    stat_card,
)
from tradeoff_app.data.sample_data import blank_study_data, clone_sample_data
from tradeoff_app.domain.models import (
    alternative_from_record,
    attribute_from_record,
    formula_from_record,
    profile_from_record,
    scenario_from_record,
    score_from_record,
    weight_entry_from_record,
)
from tradeoff_app.services.calculations import (
    build_aggregate_formula_context,
    build_formula_context,
    calculate_abs,
    calculate_weighted_abs,
    effective_weight,
    evaluate_formula_result,
    format_metric,
    get_score,
    get_weight_entry,
    normalize_scenario_weights,
    slugify_identifier,
    validate_formula,
)
from tradeoff_app.services.storage import (
    empty_study_library,
    load_study_library,
    save_study_library,
)


_INITIAL_DATA = clone_sample_data()
_DEFAULT_WEIGHT = 0.5
_DEFAULT_SCORE = 3.0


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _formula_reference_token(name: str) -> str:
    return f"formula_{slugify_identifier(name)}"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return default


def _clamp(value: Any, minimum: float, maximum: float, default: float) -> float:
    parsed = _to_float(value, default)
    return max(minimum, min(maximum, parsed))


def _migrate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    migrated = {
        "project_name": payload.get("project_name", _INITIAL_DATA["project_name"]),
        "project_description": payload.get(
            "project_description",
            _INITIAL_DATA["project_description"],
        ),
        "alternatives": payload.get("alternatives", _INITIAL_DATA["alternatives"]),
        "attributes": payload.get("attributes", _INITIAL_DATA["attributes"]),
        "scenarios": payload.get("scenarios", _INITIAL_DATA["scenarios"]),
        "profiles": payload.get("profiles") or _INITIAL_DATA["profiles"],
        "benefit_cost_risk_weights": payload.get(
            "benefit_cost_risk_weights",
            _INITIAL_DATA.get("benefit_cost_risk_weights", []),
        ),
        "benefit_cost_risk_scores": payload.get(
            "benefit_cost_risk_scores",
            _INITIAL_DATA.get("benefit_cost_risk_scores", []),
        ),
        "break_even_settings": payload.get(
            "break_even_settings",
            _INITIAL_DATA.get("break_even_settings", {"integrations_per_year": 1.0, "years": 5.0}),
        ),
        "break_even_costs": payload.get(
            "break_even_costs",
            _INITIAL_DATA.get("break_even_costs", []),
        ),
        "weights": payload.get("weights", _INITIAL_DATA["weights"]),
        "scores": payload.get("scores", _INITIAL_DATA["scores"]),
        "formulas": payload.get("formulas", _INITIAL_DATA["formulas"]),
        "active_profile_id": payload.get("active_profile_id"),
        "active_scenario_id": payload.get(
            "active_scenario_id",
            _INITIAL_DATA["active_scenario_id"],
        ),
        "active_attribute_id": payload.get(
            "active_attribute_id",
            _INITIAL_DATA["active_attribute_id"],
        ),
    }

    first_profile_id = (
        migrated["active_profile_id"]
        or (migrated["profiles"][0]["id"] if migrated["profiles"] else "")
    )
    migrated["active_profile_id"] = first_profile_id

    migrated_weights: list[dict[str, Any]] = []
    for entry in migrated["weights"]:
        migrated_weights.append(
            {
                "profile_id": entry.get("profile_id", first_profile_id),
                "scenario_id": entry.get("scenario_id", ""),
                "attribute_id": entry.get("attribute_id", ""),
                "global_weight": entry.get("global_weight", _DEFAULT_WEIGHT),
                "local_weight": entry.get("local_weight", _DEFAULT_WEIGHT),
            }
        )
    migrated["weights"] = migrated_weights

    migrated_scores: list[dict[str, Any]] = []
    for entry in migrated["scores"]:
        migrated_scores.append(
            {
                "profile_id": entry.get("profile_id", first_profile_id),
                "scenario_id": entry.get("scenario_id", ""),
                "alternative_id": entry.get("alternative_id", ""),
                "attribute_id": entry.get("attribute_id", ""),
                "score": entry.get("score", _DEFAULT_SCORE),
            }
        )
    migrated["scores"] = migrated_scores
    settings = migrated["break_even_settings"] or {}
    migrated["break_even_settings"] = {
        "integrations_per_year": settings.get("integrations_per_year", 1.0),
        "years": settings.get("years", 5.0),
    }
    migrated["break_even_costs"] = [
        {
            "alternative_id": entry.get("alternative_id", ""),
            "initial_cost": entry.get("initial_cost", 0.0),
            "integration_cost": entry.get("integration_cost", 0.0),
        }
        for entry in migrated["break_even_costs"]
    ]
    return migrated


class TradeoffState(rx.State):
    """Application state for the trade-off workbench."""

    current_study_id: str = ""
    study_library: list[dict[str, Any]] = []

    project_name: str = _INITIAL_DATA["project_name"]
    project_description: str = _INITIAL_DATA["project_description"]
    alternatives: list[dict[str, Any]] = _INITIAL_DATA["alternatives"]
    attributes: list[dict[str, Any]] = _INITIAL_DATA["attributes"]
    scenarios: list[dict[str, Any]] = _INITIAL_DATA["scenarios"]
    profiles: list[dict[str, Any]] = _INITIAL_DATA["profiles"]
    benefit_cost_risk_weights: list[dict[str, Any]] = _INITIAL_DATA.get("benefit_cost_risk_weights", [])
    benefit_cost_risk_scores: list[dict[str, Any]] = _INITIAL_DATA.get("benefit_cost_risk_scores", [])
    break_even_settings: dict[str, Any] = _INITIAL_DATA.get("break_even_settings", {"integrations_per_year": 1.0, "years": 5.0})
    break_even_costs: list[dict[str, Any]] = _INITIAL_DATA.get("break_even_costs", [])
    weights: list[dict[str, Any]] = _INITIAL_DATA["weights"]
    scores: list[dict[str, Any]] = _INITIAL_DATA["scores"]
    formulas: list[dict[str, Any]] = _INITIAL_DATA["formulas"]

    active_profile_id: str = _INITIAL_DATA["active_profile_id"]
    active_scenario_id: str = _INITIAL_DATA["active_scenario_id"]
    active_attribute_id: str = _INITIAL_DATA["active_attribute_id"]

    draft_formula_name: str = ""
    draft_formula_description: str = ""
    draft_formula_latex: str = ""
    editing_formula_id: str = ""
    draft_weight_inputs: dict[str, dict[str, str]] = {}
    draft_score_inputs: dict[str, str] = {}
    draft_cost_risk_inputs: dict[str, dict[str, str]] = {}
    draft_break_even_settings: dict[str, str] = {}
    draft_break_even_cost_inputs: dict[str, dict[str, str]] = {}

    status_message: str = "Saved study loaded."

    def _set_status(self, message: str) -> None:
        self.status_message = message

    def _weight_draft_key(self, profile_id: str, scenario_id: str, attribute_id: str) -> str:
        return f"{profile_id}:{scenario_id}:{attribute_id}"

    def _score_draft_key(self, profile_id: str, scenario_id: str, alternative_id: str) -> str:
        return f"{profile_id}:{scenario_id}:{alternative_id}"

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _snapshot(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "alternatives": self.alternatives,
            "attributes": self.attributes,
            "scenarios": self.scenarios,
            "profiles": self.profiles,
            "benefit_cost_risk_weights": self.benefit_cost_risk_weights,
            "benefit_cost_risk_scores": self.benefit_cost_risk_scores,
            "break_even_settings": self.break_even_settings,
            "break_even_costs": self.break_even_costs,
            "weights": self.weights,
            "scores": self.scores,
            "formulas": self.formulas,
            "active_profile_id": self.active_profile_id,
            "active_scenario_id": self.active_scenario_id,
            "active_attribute_id": self.active_attribute_id,
        }

    def _result_snapshot(self) -> dict[str, Any]:
        return {
            "aggregate_results": self.aggregate_result_rows,
            "scenario_results": self.profile_scenario_rows,
            "break_even_results": self.break_even_rows,
            "configured_variables": self.configured_variable_rows,
            "saved_at": self._timestamp(),
        }

    def _persist_library(self) -> None:
        save_study_library(
            {
                "version": 2,
                "active_study_id": self.current_study_id,
                "studies": self.study_library,
            }
        )

    def _upsert_current_study(self) -> None:
        if not self.current_study_id:
            self.current_study_id = _new_id("study")
        record = {
            "id": self.current_study_id,
            "name": self.project_name or "Untitled Trade Study",
            "description": self.project_description,
            "updated_at": self._timestamp(),
            "payload": self._snapshot(),
            "result_snapshot": self._result_snapshot(),
        }
        replaced = False
        next_library: list[dict[str, Any]] = []
        for study in self.study_library:
            if study["id"] == self.current_study_id:
                next_library.append(record)
                replaced = True
            else:
                next_library.append(study)
        if not replaced:
            next_library.append(record)
        self.study_library = next_library

    def _record_by_id(
        self,
        records: list[dict[str, Any]],
        record_id: str,
    ) -> dict[str, Any] | None:
        for record in records:
            if record["id"] == record_id:
                return record
        return None

    def _alternatives_domain(self):
        return [alternative_from_record(record) for record in self.alternatives]

    def _attributes_domain(self):
        return [attribute_from_record(record) for record in self.attributes]

    def _scenarios_domain(self):
        return [scenario_from_record(record) for record in self.scenarios]

    def _profiles_domain(self):
        return [profile_from_record(record) for record in self.profiles]

    def _weights_domain(self):
        return [weight_entry_from_record(record) for record in self.weights]

    def _scores_domain(self):
        return [score_from_record(record) for record in self.scores]

    def _formulas_domain(self):
        return [formula_from_record(record) for record in self.formulas]

    def _cost_risk_weight_record(self, profile_id: str) -> dict[str, Any]:
        for entry in self.benefit_cost_risk_weights:
            if entry["profile_id"] == profile_id:
                return entry
        return {"profile_id": profile_id, "alpha": 0.5, "beta": 0.5}

    def _cost_risk_score_record(self, profile_id: str, alternative_id: str) -> dict[str, Any]:
        for entry in self.benefit_cost_risk_scores:
            if entry["profile_id"] == profile_id and entry["alternative_id"] == alternative_id:
                return entry
        return {
            "profile_id": profile_id,
            "alternative_id": alternative_id,
            "cost_score": 3.0,
            "risk_score": 3.0,
        }

    def _break_even_cost_record(self, alternative_id: str) -> dict[str, Any]:
        for entry in self.break_even_costs:
            if entry["alternative_id"] == alternative_id:
                return entry
        return {
            "alternative_id": alternative_id,
            "initial_cost": 0.0,
            "integration_cost": 0.0,
        }

    def _evaluate_enabled_formula_results(
        self,
        base_context: dict[str, float],
    ) -> list[dict[str, Any]]:
        evaluation_context = dict(base_context)
        results: list[dict[str, Any]] = []
        for formula in self._formulas_domain():
            if not formula.enabled:
                continue
            value = evaluate_formula_result(formula, evaluation_context)
            results.append(
                {
                    "id": formula.id,
                    "name": formula.name,
                    "value": value,
                    "display": format_metric(value, 2),
                }
            )
            if value is not None:
                evaluation_context[_formula_reference_token(formula.name)] = value
        return results

    def _sync_active_ids(self) -> None:
        profile_ids = {profile["id"] for profile in self.profiles}
        scenario_ids = {scenario["id"] for scenario in self.scenarios}
        attribute_ids = {attribute["id"] for attribute in self.attributes}
        self.active_profile_id = (
            self.active_profile_id
            if self.active_profile_id in profile_ids
            else (self.profiles[0]["id"] if self.profiles else "")
        )
        self.active_scenario_id = (
            self.active_scenario_id
            if self.active_scenario_id in scenario_ids
            else (self.scenarios[0]["id"] if self.scenarios else "")
        )
        self.active_attribute_id = (
            self.active_attribute_id
            if self.active_attribute_id in attribute_ids
            else (self.attributes[0]["id"] if self.attributes else "")
        )

    def _ensure_consistency(self) -> None:
        retired_builtin_formula_ids = {
            "formula_abs",
            "formula_weighted_abs",
        }
        builtin_formulas = {
            formula["id"]: formula
            for formula in _INITIAL_DATA.get("formulas", [])
            if bool(formula.get("builtin", False))
        }
        next_formulas: list[dict[str, Any]] = []
        handled_formula_ids: set[str] = set()

        for formula in self.formulas:
            formula_id = formula["id"]
            if formula_id in retired_builtin_formula_ids:
                continue
            if formula_id in builtin_formulas:
                builtin = builtin_formulas[formula_id]
                next_formulas.append(
                    {
                        **builtin,
                        "enabled": bool(formula.get("enabled", builtin.get("enabled", True))),
                    }
                )
                handled_formula_ids.add(formula_id)
            else:
                next_formulas.append({**formula, "enabled": bool(formula.get("enabled", True))})
                handled_formula_ids.add(formula_id)

        for formula_id, builtin in builtin_formulas.items():
            if formula_id not in handled_formula_ids:
                next_formulas.append({**builtin, "enabled": bool(builtin.get("enabled", True))})

        self.formulas = next_formulas

        weight_keys = {
            (entry["profile_id"], entry["scenario_id"], entry["attribute_id"])
            for entry in self.weights
        }
        for profile in self.profiles:
            for scenario in self.scenarios:
                for attribute in self.attributes:
                    key = (profile["id"], scenario["id"], attribute["id"])
                    if key not in weight_keys:
                        self.weights.append(
                            {
                                "profile_id": profile["id"],
                                "scenario_id": scenario["id"],
                                "attribute_id": attribute["id"],
                                "global_weight": _DEFAULT_WEIGHT,
                                "local_weight": _DEFAULT_WEIGHT,
                            }
                        )
                        weight_keys.add(key)

        score_keys = {
            (
                entry["profile_id"],
                entry["scenario_id"],
                entry["alternative_id"],
            )
            for entry in self.scores
        }
        for profile in self.profiles:
            for scenario in self.scenarios:
                for alternative in self.alternatives:
                    key = (
                        profile["id"],
                        scenario["id"],
                        alternative["id"],
                    )
                    if key not in score_keys:
                        self.scores.append(
                            {
                                "profile_id": profile["id"],
                                "scenario_id": scenario["id"],
                                "alternative_id": alternative["id"],
                                "score": _DEFAULT_SCORE,
                            }
                        )
                        score_keys.add(key)

        weight_profiles = {entry["profile_id"] for entry in self.benefit_cost_risk_weights}
        for profile in self.profiles:
            if profile["id"] not in weight_profiles:
                self.benefit_cost_risk_weights.append(
                    {
                        "profile_id": profile["id"],
                        "alpha": 0.5,
                        "beta": 0.5,
                    }
                )

        cost_risk_keys = {
            (entry["profile_id"], entry["alternative_id"])
            for entry in self.benefit_cost_risk_scores
        }
        for profile in self.profiles:
            for alternative in self.alternatives:
                key = (profile["id"], alternative["id"])
                if key not in cost_risk_keys:
                    self.benefit_cost_risk_scores.append(
                        {
                            "profile_id": profile["id"],
                            "alternative_id": alternative["id"],
                            "cost_score": 3.0,
                            "risk_score": 3.0,
                        }
                    )
                    cost_risk_keys.add(key)

        self.break_even_settings = {
            "integrations_per_year": _clamp(
                self.break_even_settings.get("integrations_per_year", 1.0),
                0.0,
                9999.0,
                1.0,
            ),
            "years": _clamp(
                self.break_even_settings.get("years", 5.0),
                0.0,
                9999.0,
                5.0,
            ),
        }

        break_even_alt_ids = {entry["alternative_id"] for entry in self.break_even_costs}
        for alternative in self.alternatives:
            if alternative["id"] not in break_even_alt_ids:
                self.break_even_costs.append(
                    {
                        "alternative_id": alternative["id"],
                        "initial_cost": 0.0,
                        "integration_cost": 0.0,
                    }
                )
                break_even_alt_ids.add(alternative["id"])
        self.break_even_costs = [
            entry
            for entry in self.break_even_costs
            if entry["alternative_id"] in {alternative["id"] for alternative in self.alternatives}
        ]

    def _load_payload(self, payload: dict[str, Any]) -> None:
        payload = _migrate_payload(payload)
        self.project_name = payload["project_name"]
        self.project_description = payload["project_description"]
        self.alternatives = payload["alternatives"]
        self.attributes = payload["attributes"]
        self.scenarios = payload["scenarios"]
        self.profiles = payload["profiles"]
        self.benefit_cost_risk_weights = payload["benefit_cost_risk_weights"]
        self.benefit_cost_risk_scores = payload["benefit_cost_risk_scores"]
        self.break_even_settings = payload["break_even_settings"]
        self.break_even_costs = payload["break_even_costs"]
        self.weights = payload["weights"]
        self.scores = payload["scores"]
        self.formulas = payload["formulas"]
        self.active_profile_id = payload["active_profile_id"]
        self.active_scenario_id = payload["active_scenario_id"]
        self.active_attribute_id = payload["active_attribute_id"]
        self._ensure_consistency()
        self._sync_active_ids()

    def _commit(self, message: str) -> None:
        self._ensure_consistency()
        self._sync_active_ids()
        self._upsert_current_study()
        self._persist_library()
        self._set_status(message)

    def load_saved_state(self) -> None:
        library = load_study_library()
        if library is None:
            self._load_payload(clone_sample_data())
            self.current_study_id = _new_id("study")
            self.study_library = []
            self._upsert_current_study()
            self._persist_library()
            self._set_status("No saved study found. Sample data loaded.")
            return
        studies = list(library.get("studies", []))
        if not studies:
            self._load_payload(clone_sample_data())
            self.current_study_id = _new_id("study")
            self.study_library = []
            self._upsert_current_study()
            self._persist_library()
            self._set_status("No saved study found. Sample data loaded.")
            return
        active_study_id = str(library.get("active_study_id", "") or studies[0]["id"])
        active_study = next(
            (study for study in studies if study["id"] == active_study_id),
            studies[0],
        )
        self.study_library = studies
        self.current_study_id = str(active_study["id"])
        self._load_payload(active_study.get("payload", clone_sample_data()))
        self._upsert_current_study()
        self._persist_library()
        self._set_status("Saved study loaded from disk.")

    def save_now(self) -> None:
        self._ensure_consistency()
        self._sync_active_ids()
        self._upsert_current_study()
        self._persist_library()
        self._set_status("Study saved to the study library.")

    def reload_saved_state(self) -> None:
        library = load_study_library()
        if library is None or not library.get("studies"):
            self._set_status("No saved study library is available.")
            return
        self.study_library = list(library.get("studies", []))
        target_id = self.current_study_id or str(library.get("active_study_id", ""))
        study = next(
            (item for item in self.study_library if item["id"] == target_id),
            self.study_library[0],
        )
        self.current_study_id = str(study["id"])
        self._load_payload(study.get("payload", clone_sample_data()))
        self._persist_library()
        self._set_status("Saved study reloaded from the study library.")

    def reset_demo(self) -> None:
        self._load_payload(clone_sample_data())
        self._commit("Built-in sample data restored.")

    def create_new_study(self) -> None:
        self.current_study_id = _new_id("study")
        self._load_payload(blank_study_data())
        self._commit("New blank study created.")

    def load_study(self, study_id: str) -> None:
        study = self._record_by_id(self.study_library, study_id)
        if not study:
            self._set_status("The selected study could not be found.")
            return
        self.current_study_id = study_id
        self._load_payload(study.get("payload", clone_sample_data()))
        self._persist_library()
        self._set_status(f"Study '{self.project_name}' loaded.")

    def set_active_profile(self, profile_id: str) -> None:
        self.active_profile_id = profile_id

    def set_active_scenario(self, scenario_id: str) -> None:
        self.active_scenario_id = scenario_id

    def set_active_attribute(self, attribute_id: str) -> None:
        self.active_attribute_id = attribute_id

    def set_draft_formula_name(self, value: str) -> None:
        self.draft_formula_name = value

    def set_draft_formula_description(self, value: str) -> None:
        self.draft_formula_description = value

    def set_draft_formula_latex(self, value: str) -> None:
        self.draft_formula_latex = value

    def set_draft_attribute_weight(self, attribute_id: str, value: str) -> None:
        key = self._weight_draft_key(self.active_profile_id, self.active_scenario_id, attribute_id)
        current = dict(self.draft_weight_inputs.get(key, {}))
        current["attribute_weight"] = value
        self.draft_weight_inputs[key] = current

    def set_draft_local_weight(self, attribute_id: str, value: str) -> None:
        key = self._weight_draft_key(self.active_profile_id, self.active_scenario_id, attribute_id)
        current = dict(self.draft_weight_inputs.get(key, {}))
        current["local_weight"] = value
        self.draft_weight_inputs[key] = current

    def set_draft_score(self, scenario_id: str, alternative_id: str, value: str) -> None:
        key = self._score_draft_key(self.active_profile_id, scenario_id, alternative_id)
        self.draft_score_inputs[key] = value

    def set_alpha(self, value: str) -> None:
        alpha = _clamp(value, 0.0, 1.0, 0.5)
        beta = round(1.0 - alpha, 4)
        self.benefit_cost_risk_weights = [
            (
                {**entry, "alpha": alpha, "beta": beta}
                if entry["profile_id"] == self.active_profile_id
                else entry
            )
            for entry in self.benefit_cost_risk_weights
        ]
        self._commit("Benefit to cost and risk weights updated.")

    def set_beta(self, value: str) -> None:
        beta = _clamp(value, 0.0, 1.0, 0.5)
        alpha = round(1.0 - beta, 4)
        self.benefit_cost_risk_weights = [
            (
                {**entry, "alpha": alpha, "beta": beta}
                if entry["profile_id"] == self.active_profile_id
                else entry
            )
            for entry in self.benefit_cost_risk_weights
        ]
        self._commit("Benefit to cost and risk weights updated.")

    def set_draft_cost_score(self, alternative_id: str, value: str) -> None:
        key = f"{self.active_profile_id}:{alternative_id}"
        current = dict(self.draft_cost_risk_inputs.get(key, {}))
        current["cost_score"] = value
        self.draft_cost_risk_inputs[key] = current

    def set_draft_risk_score(self, alternative_id: str, value: str) -> None:
        key = f"{self.active_profile_id}:{alternative_id}"
        current = dict(self.draft_cost_risk_inputs.get(key, {}))
        current["risk_score"] = value
        self.draft_cost_risk_inputs[key] = current

    def set_draft_integrations_per_year(self, value: str) -> None:
        self.draft_break_even_settings["integrations_per_year"] = value

    def set_draft_years(self, value: str) -> None:
        self.draft_break_even_settings["years"] = value

    def set_draft_initial_cost(self, alternative_id: str, value: str) -> None:
        current = dict(self.draft_break_even_cost_inputs.get(alternative_id, {}))
        current["initial_cost"] = value
        self.draft_break_even_cost_inputs[alternative_id] = current

    def set_draft_integration_cost(self, alternative_id: str, value: str) -> None:
        current = dict(self.draft_break_even_cost_inputs.get(alternative_id, {}))
        current["integration_cost"] = value
        self.draft_break_even_cost_inputs[alternative_id] = current

    def append_formula_token(self, token: str) -> None:
        separator = "" if not self.draft_formula_latex else " "
        self.draft_formula_latex = f"{self.draft_formula_latex}{separator}{token}"

    def clear_formula_builder(self) -> None:
        self.draft_formula_name = ""
        self.draft_formula_description = ""
        self.draft_formula_latex = ""
        self.editing_formula_id = ""
        self._set_status("Formula builder cleared.")

    def update_project(self, form_data: dict[str, Any]) -> None:
        name = _clean_text(form_data.get("project_name"))
        if not name:
            self._set_status("The study name is required.")
            return
        self.project_name = name
        self.project_description = _clean_text(form_data.get("project_description"))
        self._commit("Project context updated.")

    def add_profile(self, form_data: dict[str, Any]) -> None:
        name = _clean_text(form_data.get("name"))
        if not name:
            self._set_status("Profile name is required.")
            return
        profile_id = _new_id("profile")
        self.profiles.append(
            {
                "id": profile_id,
                "name": name,
                "description": _clean_text(form_data.get("description")),
            }
        )
        self.active_profile_id = profile_id
        self._commit(f"Profile '{name}' added.")

    def remove_profile(self, profile_id: str) -> None:
        self.profiles = [profile for profile in self.profiles if profile["id"] != profile_id]
        self.weights = [entry for entry in self.weights if entry["profile_id"] != profile_id]
        self.scores = [entry for entry in self.scores if entry["profile_id"] != profile_id]
        self._commit("Profile removed.")

    def add_alternative(self, form_data: dict[str, Any]) -> None:
        name = _clean_text(form_data.get("name"))
        if not name:
            self._set_status("Alternative name is required.")
            return
        self.alternatives.append(
            {
                "id": _new_id("alt"),
                "name": name,
                "description": _clean_text(form_data.get("description")),
            }
        )
        self._commit(f"Alternative '{name}' added.")

    def remove_alternative(self, alternative_id: str) -> None:
        self.alternatives = [
            alternative for alternative in self.alternatives if alternative["id"] != alternative_id
        ]
        self.scores = [entry for entry in self.scores if entry["alternative_id"] != alternative_id]
        self.benefit_cost_risk_scores = [
            entry for entry in self.benefit_cost_risk_scores if entry["alternative_id"] != alternative_id
        ]
        self.break_even_costs = [
            entry for entry in self.break_even_costs if entry["alternative_id"] != alternative_id
        ]
        self._commit("Alternative removed.")

    def add_attribute(self, form_data: dict[str, Any]) -> None:
        name = _clean_text(form_data.get("name"))
        if not name:
            self._set_status("Attribute name is required.")
            return
        attribute_id = _new_id("attr")
        self.attributes.append(
            {
                "id": attribute_id,
                "name": name,
                "description": _clean_text(form_data.get("description")),
            }
        )
        self.active_attribute_id = attribute_id
        self._commit(f"Attribute '{name}' added.")

    def remove_attribute(self, attribute_id: str) -> None:
        self.attributes = [attribute for attribute in self.attributes if attribute["id"] != attribute_id]
        self.weights = [entry for entry in self.weights if entry["attribute_id"] != attribute_id]
        self._commit("Attribute removed.")

    def add_scenario(self, form_data: dict[str, Any]) -> None:
        name = _clean_text(form_data.get("name"))
        if not name:
            self._set_status("Scenario name is required.")
            return
        scenario_id = _new_id("scenario")
        self.scenarios.append(
            {
                "id": scenario_id,
                "name": name,
                "description": _clean_text(form_data.get("description")),
                "weight": _clamp(form_data.get("weight"), 0.0, 1.0, _DEFAULT_WEIGHT),
            }
        )
        self.active_scenario_id = scenario_id
        self._commit(f"Scenario '{name}' added.")

    def remove_scenario(self, scenario_id: str) -> None:
        self.scenarios = [scenario for scenario in self.scenarios if scenario["id"] != scenario_id]
        self.weights = [entry for entry in self.weights if entry["scenario_id"] != scenario_id]
        self.scores = [entry for entry in self.scores if entry["scenario_id"] != scenario_id]
        self._commit("Scenario removed.")

    def save_scenario_weight(self, form_data: dict[str, Any]) -> None:
        scenario_id = _clean_text(form_data.get("scenario_id"))
        weight = _clamp(form_data.get("weight"), 0.0, 1.0, _DEFAULT_WEIGHT)
        self.scenarios = [
            {**scenario, "weight": weight} if scenario["id"] == scenario_id else scenario
            for scenario in self.scenarios
        ]
        self._commit("Scenario weight updated.")

    def save_weight_entry(self, form_data: dict[str, Any]) -> None:
        profile_id = _clean_text(form_data.get("profile_id"))
        scenario_id = _clean_text(form_data.get("scenario_id"))
        attribute_id = _clean_text(form_data.get("attribute_id"))
        attribute_weight = _clamp(form_data.get("attribute_weight"), 0.0, 1.0, _DEFAULT_WEIGHT)
        local_weight = _clamp(form_data.get("local_weight"), 0.0, 1.0, _DEFAULT_WEIGHT)
        updated = False
        next_entries: list[dict[str, Any]] = []
        for entry in self.weights:
            if (
                entry["profile_id"] == profile_id
                and entry["scenario_id"] == scenario_id
                and entry["attribute_id"] == attribute_id
            ):
                next_entries.append(
                    {
                        **entry,
                        "global_weight": attribute_weight,
                        "local_weight": local_weight,
                    }
                )
                updated = True
            else:
                next_entries.append(entry)
        if not updated:
            next_entries.append(
                {
                    "profile_id": profile_id,
                    "scenario_id": scenario_id,
                    "attribute_id": attribute_id,
                    "global_weight": attribute_weight,
                    "local_weight": local_weight,
                }
            )
        self.weights = next_entries
        self._commit("Profile weights updated.")

    def save_weight_row(self, attribute_id: str) -> None:
        key = self._weight_draft_key(self.active_profile_id, self.active_scenario_id, attribute_id)
        draft = self.draft_weight_inputs.get(key)
        entry = get_weight_entry(
            self._weights_domain(),
            self.active_profile_id,
            self.active_scenario_id,
            attribute_id,
        )
        self.save_weight_entry(
            {
                "profile_id": self.active_profile_id,
                "scenario_id": self.active_scenario_id,
                "attribute_id": attribute_id,
                "attribute_weight": (draft or {}).get("attribute_weight", str(entry.global_weight)),
                "local_weight": (draft or {}).get("local_weight", str(entry.local_weight)),
            }
        )

    def save_all_weight_rows(self) -> None:
        profile_id = self.active_profile_id
        scenario_id = self.active_scenario_id
        next_entries: list[dict[str, Any]] = []
        targeted_attribute_ids = {attribute["id"] for attribute in self.attributes}

        for entry in self.weights:
            if (
                entry["profile_id"] == profile_id
                and entry["scenario_id"] == scenario_id
                and entry["attribute_id"] in targeted_attribute_ids
            ):
                key = self._weight_draft_key(profile_id, scenario_id, entry["attribute_id"])
                draft = self.draft_weight_inputs.get(key, {})
                next_entries.append(
                    {
                        **entry,
                        "global_weight": _clamp(
                            draft.get("attribute_weight", entry["global_weight"]),
                            0.0,
                            1.0,
                            entry["global_weight"],
                        ),
                        "local_weight": _clamp(
                            draft.get("local_weight", entry["local_weight"]),
                            0.0,
                            1.0,
                            entry["local_weight"],
                        ),
                    }
                )
            else:
                next_entries.append(entry)

        existing_keys = {
            (entry["profile_id"], entry["scenario_id"], entry["attribute_id"])
            for entry in next_entries
        }
        for attribute in self.attributes:
            key = self._weight_draft_key(profile_id, scenario_id, attribute["id"])
            draft = self.draft_weight_inputs.get(key, {})
            entry_key = (profile_id, scenario_id, attribute["id"])
            if entry_key not in existing_keys:
                next_entries.append(
                    {
                        "profile_id": profile_id,
                        "scenario_id": scenario_id,
                        "attribute_id": attribute["id"],
                        "global_weight": _clamp(
                            draft.get("attribute_weight", _DEFAULT_WEIGHT),
                            0.0,
                            1.0,
                            _DEFAULT_WEIGHT,
                        ),
                        "local_weight": _clamp(
                            draft.get("local_weight", _DEFAULT_WEIGHT),
                            0.0,
                            1.0,
                            _DEFAULT_WEIGHT,
                        ),
                    }
                )

        self.weights = next_entries
        self._commit("All profile attribute weights updated.")

    def save_score(self, form_data: dict[str, Any]) -> None:
        profile_id = _clean_text(form_data.get("profile_id"))
        scenario_id = _clean_text(form_data.get("scenario_id"))
        alternative_id = _clean_text(form_data.get("alternative_id"))
        score = _clamp(form_data.get("score"), 1.0, 5.0, _DEFAULT_SCORE)
        updated = False
        next_scores: list[dict[str, Any]] = []
        for entry in self.scores:
            if (
                entry["profile_id"] == profile_id
                and entry["scenario_id"] == scenario_id
                and entry["alternative_id"] == alternative_id
            ):
                next_scores.append({**entry, "score": score})
                updated = True
            else:
                next_scores.append(entry)
        if not updated:
            next_scores.append(
                {
                    "profile_id": profile_id,
                    "scenario_id": scenario_id,
                    "alternative_id": alternative_id,
                    "score": score,
                }
            )
        self.scores = next_scores
        self._commit("Profile score updated.")

    def save_all_scores(self) -> None:
        profile_id = self.active_profile_id
        targeted_keys = {
            (profile_id, scenario["id"], alternative["id"])
            for scenario in self.scenarios
            for alternative in self.alternatives
        }
        next_scores: list[dict[str, Any]] = []
        existing_keys = set()

        for entry in self.scores:
            entry_key = (
                entry["profile_id"],
                entry["scenario_id"],
                entry["alternative_id"],
            )
            if entry_key in targeted_keys:
                draft_key = self._score_draft_key(*entry_key)
                next_scores.append(
                    {
                        **entry,
                        "score": _clamp(
                            self.draft_score_inputs.get(draft_key, entry["score"]),
                            1.0,
                            5.0,
                            entry["score"],
                        ),
                    }
                )
                existing_keys.add(entry_key)
            else:
                next_scores.append(entry)

        for scenario in self.scenarios:
            for alternative in self.alternatives:
                entry_key = (profile_id, scenario["id"], alternative["id"])
                if entry_key not in existing_keys:
                    draft_key = self._score_draft_key(*entry_key)
                    next_scores.append(
                        {
                            "profile_id": profile_id,
                            "scenario_id": scenario["id"],
                            "alternative_id": alternative["id"],
                            "score": _clamp(
                                self.draft_score_inputs.get(draft_key, _DEFAULT_SCORE),
                                1.0,
                                5.0,
                                _DEFAULT_SCORE,
                            ),
                        }
                    )

        self.scores = next_scores
        self._commit("All profile scenario scores updated.")

    def save_all_cost_risk_scores(self) -> None:
        profile_id = self.active_profile_id
        next_entries: list[dict[str, Any]] = []
        existing_keys = set()

        for entry in self.benefit_cost_risk_scores:
            if entry["profile_id"] == profile_id:
                key = f"{profile_id}:{entry['alternative_id']}"
                draft = self.draft_cost_risk_inputs.get(key, {})
                next_entries.append(
                    {
                        **entry,
                        "cost_score": _clamp(
                            draft.get("cost_score", entry["cost_score"]),
                            1.0,
                            5.0,
                            entry["cost_score"],
                        ),
                        "risk_score": _clamp(
                            draft.get("risk_score", entry["risk_score"]),
                            1.0,
                            5.0,
                            entry["risk_score"],
                        ),
                    }
                )
                existing_keys.add(entry["alternative_id"])
            else:
                next_entries.append(entry)

        for alternative in self.alternatives:
            if alternative["id"] not in existing_keys:
                key = f"{profile_id}:{alternative['id']}"
                draft = self.draft_cost_risk_inputs.get(key, {})
                next_entries.append(
                    {
                        "profile_id": profile_id,
                        "alternative_id": alternative["id"],
                        "cost_score": _clamp(draft.get("cost_score", 3.0), 1.0, 5.0, 3.0),
                        "risk_score": _clamp(draft.get("risk_score", 3.0), 1.0, 5.0, 3.0),
                    }
                )

        self.benefit_cost_risk_scores = next_entries
        self._commit("Benefit to cost and risk scores updated.")

    def save_break_even_model(self) -> None:
        integrations_per_year = _clamp(
            self.draft_break_even_settings.get(
                "integrations_per_year",
                self.break_even_settings.get("integrations_per_year", 1.0),
            ),
            0.0,
            9999.0,
            1.0,
        )
        years = _clamp(
            self.draft_break_even_settings.get(
                "years",
                self.break_even_settings.get("years", 5.0),
            ),
            0.0,
            9999.0,
            5.0,
        )
        self.break_even_settings = {
            "integrations_per_year": integrations_per_year,
            "years": years,
        }

        next_entries: list[dict[str, Any]] = []
        existing_ids = set()
        for entry in self.break_even_costs:
            alternative_id = entry["alternative_id"]
            draft = self.draft_break_even_cost_inputs.get(alternative_id, {})
            next_entries.append(
                {
                    **entry,
                    "initial_cost": _clamp(
                        draft.get("initial_cost", entry.get("initial_cost", 0.0)),
                        0.0,
                        999999999.0,
                        entry.get("initial_cost", 0.0),
                    ),
                    "integration_cost": _clamp(
                        draft.get("integration_cost", entry.get("integration_cost", 0.0)),
                        0.0,
                        999999999.0,
                        entry.get("integration_cost", 0.0),
                    ),
                }
            )
            existing_ids.add(alternative_id)

        for alternative in self.alternatives:
            if alternative["id"] not in existing_ids:
                draft = self.draft_break_even_cost_inputs.get(alternative["id"], {})
                next_entries.append(
                    {
                        "alternative_id": alternative["id"],
                        "initial_cost": _clamp(
                            draft.get("initial_cost", 0.0),
                            0.0,
                            999999999.0,
                            0.0,
                        ),
                        "integration_cost": _clamp(
                            draft.get("integration_cost", 0.0),
                            0.0,
                            999999999.0,
                            0.0,
                        ),
                    }
                )

        self.break_even_costs = next_entries
        self._commit("Break-even cost model updated.")

    def save_formula(self) -> None:
        name = _clean_text(self.draft_formula_name)
        latex = _clean_text(self.draft_formula_latex)
        if not name or not latex:
            self._set_status("Formula name and LaTeX expression are required.")
            return
        is_valid, error_message = validate_formula(
            latex,
            {item["token"] for item in self.formula_variable_catalog},
        )
        if not is_valid:
            self._set_status(f"Invalid formula: {error_message}")
            return
        description = _clean_text(self.draft_formula_description)
        if self.editing_formula_id:
            self.formulas = [
                (
                    {
                        **formula,
                        "name": name,
                        "latex": latex,
                        "description": description,
                    }
                    if formula["id"] == self.editing_formula_id and not formula.get("builtin", False)
                    else formula
                )
                for formula in self.formulas
            ]
            status = f"Formula '{name}' updated."
        else:
            self.formulas.append(
                {
                    "id": _new_id("formula"),
                    "name": name,
                    "latex": latex,
                    "description": description,
                    "builtin": False,
                    "enabled": True,
                }
            )
            status = f"Formula '{name}' added."
        self.draft_formula_name = ""
        self.draft_formula_description = ""
        self.draft_formula_latex = ""
        self.editing_formula_id = ""
        self._commit(status)

    def start_edit_formula(self, formula_id: str) -> None:
        formula = self._record_by_id(self.formulas, formula_id)
        if not formula or formula.get("builtin", False):
            self._set_status("Built-in formulas cannot be edited.")
            return
        self.editing_formula_id = formula_id
        self.draft_formula_name = str(formula.get("name", ""))
        self.draft_formula_description = str(formula.get("description", ""))
        self.draft_formula_latex = str(formula.get("latex", ""))
        self._set_status(f"Editing formula '{self.draft_formula_name}'.")

    def remove_formula(self, formula_id: str) -> None:
        self.formulas = [
            formula
            for formula in self.formulas
            if not (formula["id"] == formula_id and not formula.get("builtin", False))
        ]
        if self.editing_formula_id == formula_id:
            self.draft_formula_name = ""
            self.draft_formula_description = ""
            self.draft_formula_latex = ""
            self.editing_formula_id = ""
        self._commit("Formula removed.")

    def toggle_formula_enabled(self, formula_id: str) -> None:
        self.formulas = [
            (
                {
                    **formula,
                    "enabled": not bool(formula.get("enabled", True)),
                }
                if formula["id"] == formula_id
                else formula
            )
            for formula in self.formulas
        ]
        self._commit("Formula availability updated.")

    @rx.var(cache=True)
    def profile_options(self) -> list[dict[str, str]]:
        return [{"value": item["id"], "label": item["name"]} for item in self.profiles]

    @rx.var(cache=True)
    def scenario_options(self) -> list[dict[str, str]]:
        return [{"value": item["id"], "label": item["name"]} for item in self.scenarios]

    @rx.var(cache=True)
    def attribute_options(self) -> list[dict[str, str]]:
        return [{"value": item["id"], "label": item["name"]} for item in self.attributes]

    @rx.var(cache=True)
    def series_meta(self) -> list[dict[str, str]]:
        return [
            {"name": alternative["name"], "color": SERIES_COLORS[index % len(SERIES_COLORS)]}
            for index, alternative in enumerate(self.alternatives)
        ]

    @rx.var(cache=True)
    def selected_profile_name(self) -> str:
        profile = self._record_by_id(self.profiles, self.active_profile_id)
        return profile["name"] if profile else "No profile selected"

    @rx.var(cache=True)
    def is_editing_formula(self) -> bool:
        return bool(self.editing_formula_id)

    @rx.var(cache=True)
    def current_study_name(self) -> str:
        study = self._record_by_id(self.study_library, self.current_study_id)
        return str(study.get("name", self.project_name)) if study else self.project_name

    @rx.var(cache=True)
    def study_library_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for study in self.study_library:
            payload = study.get("payload", {})
            rows.append(
                {
                    "id": study["id"],
                    "name": study.get("name", "Untitled Trade Study"),
                    "description": study.get("description", ""),
                    "updated_at": study.get("updated_at", ""),
                    "alternatives": len(payload.get("alternatives", [])),
                    "scenarios": len(payload.get("scenarios", [])),
                    "profiles": len(payload.get("profiles", [])),
                    "is_current": study["id"] == self.current_study_id,
                }
            )
        rows.sort(key=lambda row: row["updated_at"], reverse=True)
        return rows

    @rx.var(cache=True)
    def formula_variable_catalog(self) -> list[dict[str, str]]:
        catalog = [
            {"token": "abs", "label": "ABS", "group": "Built-in"},
            {"token": "Benefit(A)", "label": "Benefit(A)", "group": "Built-in"},
            {"token": "num_scenarios", "label": "Number of scenarios", "group": "Built-in"},
            {"token": "alpha", "label": "Cost weight alpha", "group": "Built-in"},
            {"token": "beta", "label": "Risk weight beta", "group": "Built-in"},
            {"token": "cost_score", "label": "Cost score", "group": "Built-in"},
            {"token": "cost_score(A)", "label": "Cost score(A)", "group": "Built-in"},
            {"token": "risk_score", "label": "Risk score", "group": "Built-in"},
            {"token": "risk_score(A)", "label": "Risk score(A)", "group": "Built-in"},
            {"token": "scenario_weight", "label": "Scenario weight", "group": "Built-in"},
            {"token": "normalized_scenario_weight", "label": "Normalized scenario weight", "group": "Built-in"},
            {"token": "weighted_abs", "label": "Scenario weighted ABS", "group": "Built-in"},
            {"token": "score_i", "label": "Indexed scenario score", "group": "Indexed"},
            {"token": "weighted_abs_i", "label": "Indexed weighted ABS", "group": "Indexed"},
            {"token": "global_weight_i", "label": "Indexed total global weight", "group": "Indexed"},
            {"token": r"\sum_{i=1}^{num_scenarios}(weighted_abs_i)", "label": "Indexed summation template", "group": "Indexed"},
            {"token": r"\sum_{score_*}", "label": "Sum of all score variables", "group": "Summation"},
            {"token": r"\sum_{attribute_weight_*}", "label": "Sum of all attribute weight variables", "group": "Summation"},
            {"token": r"\sum_{global_weight_*}", "label": "Sum of all global weight variables", "group": "Summation"},
            {"token": r"\sum_{local_weight_*}", "label": "Sum of all local weight variables", "group": "Summation"},
            {"token": r"\sum_{effective_weight_*}", "label": "Sum of all effective weight variables", "group": "Summation"},
            {"token": r"\sum_{contribution_*}", "label": "Sum of all contribution variables", "group": "Summation"},
        ]
        for attribute in self.attributes:
            slug = slugify_identifier(attribute["name"])
            catalog.extend(
                [
                    {"token": f"score_{slug}", "label": f"{attribute['name']} score", "group": "Score"},
                    {"token": f"attribute_weight_{slug}", "label": f"{attribute['name']} attribute weight", "group": "Weight"},
                    {"token": f"global_weight_{slug}", "label": f"{attribute['name']} global weight", "group": "Weight"},
                    {"token": f"local_weight_{slug}", "label": f"{attribute['name']} local weight", "group": "Weight"},
                    {"token": f"effective_weight_{slug}", "label": f"{attribute['name']} global weight alias", "group": "Weight"},
                    {"token": f"contribution_{slug}", "label": f"{attribute['name']} contribution", "group": "Contribution"},
                ]
            )
        catalog.extend(
            [
                {
                    "token": _formula_reference_token(formula["name"]),
                    "label": f"{formula['name']} formula result",
                    "group": "Registered Formula",
                }
                for formula in self.formulas
                if not bool(formula.get("builtin", False))
            ]
        )
        return sorted(catalog, key=lambda item: (item["token"].lower(), item["label"].lower()))

    @rx.var(cache=True)
    def profile_rows(self) -> list[dict[str, Any]]:
        return self.profiles

    @rx.var(cache=True)
    def scenario_rows(self) -> list[dict[str, Any]]:
        return [
            {
                **scenario,
                "weight_display": format_metric(float(scenario["weight"]), 2),
            }
            for scenario in self.scenarios
        ]

    @rx.var(cache=True)
    def benefit_cost_risk_weight_row(self) -> dict[str, str]:
        record = self._cost_risk_weight_record(self.active_profile_id)
        return {
            "alpha": format_metric(float(record.get("alpha", 0.5)), 2),
            "beta": format_metric(float(record.get("beta", 0.5)), 2),
        }

    @rx.var(cache=True)
    def benefit_cost_risk_score_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        weight_record = self._cost_risk_weight_record(self.active_profile_id)
        alpha = float(weight_record.get("alpha", 0.5))
        beta = float(weight_record.get("beta", 0.5))
        for alternative in self.alternatives:
            record = self._cost_risk_score_record(self.active_profile_id, alternative["id"])
            key = f"{self.active_profile_id}:{alternative['id']}"
            draft = self.draft_cost_risk_inputs.get(key, {})
            cost_score = float(record.get("cost_score", 3.0))
            risk_score = float(record.get("risk_score", 3.0))
            rows.append(
                {
                    "alternative_id": alternative["id"],
                    "alternative_name": alternative["name"],
                    "cost_score": draft.get("cost_score", str(record.get("cost_score", 3.0))),
                    "risk_score": draft.get("risk_score", str(record.get("risk_score", 3.0))),
                    "cost_score_display": format_metric(cost_score * alpha, 2),
                    "risk_score_display": format_metric(risk_score * beta, 2),
                }
            )
        return rows

    @rx.var(cache=True)
    def break_even_model_row(self) -> dict[str, str]:
        return {
            "integrations_per_year": self.draft_break_even_settings.get(
                "integrations_per_year",
                format_metric(
                    _to_float(self.break_even_settings.get("integrations_per_year", 1.0), 1.0),
                    2,
                ),
            ),
            "years": self.draft_break_even_settings.get(
                "years",
                format_metric(_to_float(self.break_even_settings.get("years", 5.0), 5.0), 2),
            ),
            "total_integrations": format_metric(self.break_even_total_integrations_value, 2),
        }

    @rx.var(cache=True)
    def break_even_total_integrations_value(self) -> float:
        integrations_per_year = _to_float(self.break_even_settings.get("integrations_per_year", 1.0), 1.0)
        years = _to_float(self.break_even_settings.get("years", 5.0), 5.0)
        return round(max(integrations_per_year, 0.0) * max(years, 0.0), 4)

    @rx.var(cache=True)
    def break_even_cost_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        total_integrations = self.break_even_total_integrations_value
        for alternative in self.alternatives:
            record = self._break_even_cost_record(alternative["id"])
            draft = self.draft_break_even_cost_inputs.get(alternative["id"], {})
            initial_cost = _to_float(record.get("initial_cost", 0.0), 0.0)
            integration_cost = _to_float(record.get("integration_cost", 0.0), 0.0)
            rows.append(
                {
                    "alternative_id": alternative["id"],
                    "alternative_name": alternative["name"],
                    "initial_cost": draft.get("initial_cost", format_metric(initial_cost, 2)),
                    "integration_cost": draft.get("integration_cost", format_metric(integration_cost, 2)),
                    "tco_display": format_metric(initial_cost + (total_integrations * integration_cost), 2),
                }
            )
        return rows

    @rx.var(cache=True)
    def break_even_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        integrations_per_year = _to_float(self.break_even_settings.get("integrations_per_year", 1.0), 1.0)
        total_integrations = self.break_even_total_integrations_value
        for index, left in enumerate(self.alternatives):
            left_cost = self._break_even_cost_record(left["id"])
            left_initial = _to_float(left_cost.get("initial_cost", 0.0), 0.0)
            left_integration = _to_float(left_cost.get("integration_cost", 0.0), 0.0)
            for right in self.alternatives[index + 1 :]:
                right_cost = self._break_even_cost_record(right["id"])
                right_initial = _to_float(right_cost.get("initial_cost", 0.0), 0.0)
                right_integration = _to_float(right_cost.get("integration_cost", 0.0), 0.0)
                denominator = left_integration - right_integration
                exact_break_even: float | None = None
                first_whole: int | None = None
                status = "No break-even"

                if abs(denominator) < 1e-9:
                    status = "Same integration slope"
                    if abs(left_initial - right_initial) < 1e-9:
                        status = "Equivalent at every integration count"
                        exact_break_even = 1.0
                        first_whole = 1
                else:
                    exact = (right_initial - left_initial) / denominator
                    if exact >= 0:
                        effective_exact = max(1.0, exact)
                        exact_break_even = round(effective_exact, 4)
                        first_whole = max(1, int(math.ceil(exact)))
                        status = (
                            "Within modeled horizon"
                            if effective_exact <= total_integrations
                            else "Beyond modeled horizon"
                        )
                    else:
                        status = "Dominated from the start"

                years_display = "N/A"
                if first_whole is not None and integrations_per_year > 0:
                    years_display = format_metric(first_whole / integrations_per_year, 2)

                rows.append(
                    {
                        "comparison": f"{left['name']} vs {right['name']}",
                        "exact_break_even": format_metric(exact_break_even, 2) if exact_break_even is not None else "N/A",
                        "first_whole_integration": str(first_whole) if first_whole is not None else "N/A",
                        "break_even_year": years_display,
                        "status": status,
                    }
                )
        return rows

    @rx.var(cache=True)
    def break_even_chart_data(self) -> list[dict[str, Any]]:
        if not self.alternatives:
            return []
        max_integrations = max(1, int(math.ceil(self.break_even_total_integrations_value)))
        rows: list[dict[str, Any]] = []
        cost_records = {
            alternative["id"]: self._break_even_cost_record(alternative["id"])
            for alternative in self.alternatives
        }
        for integrations in range(max_integrations + 1):
            row: dict[str, Any] = {"integrations": integrations}
            for alternative in self.alternatives:
                record = cost_records[alternative["id"]]
                initial_cost = _to_float(record.get("initial_cost", 0.0), 0.0)
                integration_cost = _to_float(record.get("integration_cost", 0.0), 0.0)
                row[alternative["name"]] = round(initial_cost + (integrations * integration_cost), 4)
            rows.append(row)
        return rows

    @rx.var(cache=True)
    def weight_matrix_rows(self) -> list[dict[str, Any]]:
        entries = self._weights_domain()
        rows: list[dict[str, Any]] = []
        for attribute in self.attributes:
            entry = get_weight_entry(
                entries,
                self.active_profile_id,
                self.active_scenario_id,
                attribute["id"],
            )
            draft = self.draft_weight_inputs.get(
                self._weight_draft_key(
                    self.active_profile_id,
                    self.active_scenario_id,
                    attribute["id"],
                ),
                {},
            )
            attribute_weight_value = draft.get("attribute_weight", str(entry.global_weight))
            local_weight_value = draft.get("local_weight", str(entry.local_weight))
            computed_global_weight = format_metric(
                _clamp(attribute_weight_value, 0.0, 1.0, entry.global_weight)
                * _clamp(local_weight_value, 0.0, 1.0, entry.local_weight),
                2,
            )
            rows.append(
                {
                    "id": attribute["id"],
                    "attribute": attribute["name"],
                    "description": attribute["description"],
                    "attribute_weight": attribute_weight_value,
                    "local_weight": local_weight_value,
                    "global_weight": computed_global_weight,
                }
            )
        return rows

    @rx.var(cache=True)
    def score_matrix_rows(self) -> list[dict[str, Any]]:
        score_entries = self._scores_domain()
        rows: list[dict[str, Any]] = []
        for scenario in self.scenarios:
            for alternative in self.alternatives:
                score = get_score(
                    score_entries,
                    self.active_profile_id,
                    scenario["id"],
                    alternative["id"],
                    default=_DEFAULT_SCORE,
                )
                draft_key = self._score_draft_key(
                    self.active_profile_id,
                    scenario["id"],
                    alternative["id"],
                )
                draft_score = self.draft_score_inputs.get(draft_key, str(score))
                rows.append(
                    {
                        "alternative_id": alternative["id"],
                        "alternative_name": alternative["name"],
                        "scenario_id": scenario["id"],
                        "scenario_name": scenario["name"],
                        "score": draft_score,
                        "score_display": format_metric(score, 2),
                    }
                )
        return rows

    @rx.var(cache=True)
    def profile_scenario_rows(self) -> list[dict[str, Any]]:
        normalized_weights = normalize_scenario_weights(self._scenarios_domain())
        rows: list[dict[str, Any]] = []
        for scenario in self._scenarios_domain():
            for alternative in self._alternatives_domain():
                abs_value = calculate_abs(
                    alternative=alternative,
                    profile_id=self.active_profile_id,
                    scenario_id=scenario.id,
                    attributes=self._attributes_domain(),
                    weight_entries=self._weights_domain(),
                    scores=self._scores_domain(),
                )
                weighted_abs = calculate_weighted_abs(
                    abs_value,
                    normalized_weights.get(scenario.id, 0.0),
                )
                tradeoff_weights = self._cost_risk_weight_record(self.active_profile_id)
                tradeoff_scores = self._cost_risk_score_record(
                    self.active_profile_id,
                    alternative.id,
                )
                context = build_formula_context(
                    alternative=alternative,
                    profile_id=self.active_profile_id,
                    scenario=scenario,
                    scenarios=self._scenarios_domain(),
                    normalized_scenario_weight=normalized_weights.get(scenario.id, 0.0),
                    normalized_scenario_weights=normalized_weights,
                    attributes=self._attributes_domain(),
                    weight_entries=self._weights_domain(),
                    scores=self._scores_domain(),
                    alpha=float(tradeoff_weights.get("alpha", 0.5)),
                    beta=float(tradeoff_weights.get("beta", 0.5)),
                    cost_score=float(tradeoff_scores.get("cost_score", 3.0)),
                    risk_score=float(tradeoff_scores.get("risk_score", 3.0)),
                    abs_value=abs_value,
                )
                formula_results = self._evaluate_enabled_formula_results(context)
                formula_summary = " | ".join(
                    f"{result['name']}: {result['display']}"
                    for result in formula_results
                )
                row: dict[str, Any] = {
                    "scenario": scenario.name,
                    "alternative": alternative.name,
                    "scenario_weight": format_metric(scenario.weight, 2),
                    "normalized_scenario_weight": format_metric(
                        normalized_weights.get(scenario.id, 0.0),
                        2,
                    ),
                    "abs_value": abs_value,
                    "abs_display": format_metric(abs_value, 2),
                    "weighted_abs_value": weighted_abs,
                    "weighted_abs_display": format_metric(weighted_abs, 2),
                    "formula_summary": formula_summary,
                }
                for result in formula_results:
                    row[f"formula_{result['id']}"] = result["display"]
                rows.append(row)
        return rows

    @rx.var(cache=True)
    def enabled_formula_columns(self) -> list[dict[str, str]]:
        return [
            {"id": formula["id"], "name": formula["name"]}
            for formula in self.formulas
            if bool(formula.get("enabled", True))
        ]

    @rx.var(cache=True)
    def registered_formula_rows(self) -> list[dict[str, Any]]:
        return sorted(
            self.formulas,
            key=lambda formula: (
                str(formula.get("name", "")).lower(),
                str(formula.get("id", "")).lower(),
            ),
        )

    @rx.var(cache=True)
    def aggregate_result_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        benefit_cost_risk_formula = next(
            (
                formula
                for formula in self._formulas_domain()
                if formula.id == "formula_benefit_cost_risk"
                or formula.name == "Benefit to Cost and Risk"
            ),
            None,
        )
        total_integrations = self.break_even_total_integrations_value
        for alternative in self._alternatives_domain():
            break_even_costs = self._break_even_cost_record(alternative.id)
            initial_cost = _to_float(break_even_costs.get("initial_cost", 0.0), 0.0)
            integration_cost = _to_float(break_even_costs.get("integration_cost", 0.0), 0.0)
            tco_value = round(initial_cost + (total_integrations * integration_cost), 4)
            context = build_aggregate_formula_context(
                alternative=alternative,
                profile_id=self.active_profile_id,
                scenarios=self._scenarios_domain(),
                attributes=self._attributes_domain(),
                weight_entries=self._weights_domain(),
                scores=self._scores_domain(),
                alpha=float(self._cost_risk_weight_record(self.active_profile_id).get("alpha", 0.5)),
                beta=float(self._cost_risk_weight_record(self.active_profile_id).get("beta", 0.5)),
                cost_score=float(self._cost_risk_score_record(self.active_profile_id, alternative.id).get("cost_score", 3.0)),
                risk_score=float(self._cost_risk_score_record(self.active_profile_id, alternative.id).get("risk_score", 3.0)),
            )
            formula_results = self._evaluate_enabled_formula_results(context)
            benefit_a_value = float(context.get("benefit_a", 0.0))
            benefit_cost_risk_value = (
                evaluate_formula_result(benefit_cost_risk_formula, context)
                if benefit_cost_risk_formula is not None
                else None
            )
            row: dict[str, Any] = {
                "alternative": alternative.name,
                "tco": format_metric(tco_value, 2),
                "tco_value": tco_value,
                "benefit_a": format_metric(benefit_a_value, 2),
                "benefit_a_value": benefit_a_value,
                "benefit_cost_risk": format_metric(benefit_cost_risk_value, 2),
                "benefit_cost_risk_value": benefit_cost_risk_value,
            }
            primary_total = 0.0
            for index, result in enumerate(formula_results):
                if index == 0 and result["value"] is not None:
                    primary_total = result["value"]
                row[f"formula_{result['id']}"] = result["display"]
                row[f"formula_{result['id']}_value"] = result["value"]
            row["aggregate_value"] = round(primary_total, 4)
            rows.append(row)
        rows.sort(key=lambda row: float(row["aggregate_value"]), reverse=True)
        return rows

    @rx.var(cache=True)
    def aggregate_formula_maxima(self) -> dict[str, str]:
        maxima: dict[str, float] = {}
        for row in self.aggregate_result_rows:
            for formula in self.enabled_formula_columns:
                key = f"formula_{formula['id']}_value"
                value = row.get(key)
                if value is None:
                    continue
                current = maxima.get(formula["id"])
                if current is None or float(value) > current:
                    maxima[formula["id"]] = float(value)
        return {formula_id: format_metric(value, 2) for formula_id, value in maxima.items()}

    @rx.var(cache=True)
    def aggregate_tco_minimum(self) -> str:
        tco_values = [
            float(row["tco_value"])
            for row in self.aggregate_result_rows
            if row.get("tco_value") is not None
        ]
        if not tco_values:
            return ""
        return format_metric(min(tco_values), 2)

    @rx.var(cache=True)
    def configured_variable_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        weights = self._weights_domain()
        scores = self._scores_domain()
        for scenario in self.scenarios:
            for alternative in self.alternatives:
                for attribute in self.attributes:
                    entry = get_weight_entry(
                        weights,
                        self.active_profile_id,
                        scenario["id"],
                        attribute["id"],
                    )
                    score = get_score(
                        scores,
                        self.active_profile_id,
                        scenario["id"],
                        alternative["id"],
                        default=_DEFAULT_SCORE,
                    )
                    contribution = effective_weight(entry) * score
                    rows.append(
                        {
                            "scenario": scenario["name"],
                            "alternative": alternative["name"],
                            "attribute": attribute["name"],
                            "scenario_weight": format_metric(float(scenario["weight"]), 2),
                            "attribute_weight": format_metric(entry.global_weight, 2),
                            "local_weight": format_metric(entry.local_weight, 2),
                            "global_weight": format_metric(effective_weight(entry), 2),
                            "score": format_metric(score, 2),
                            "contribution": format_metric(contribution, 2),
                        }
                    )
        return rows

    @rx.var(cache=True)
    def aggregate_chart_data(self) -> list[dict[str, Any]]:
        metrics = [
            ("Benefit(A)", "benefit_a_value"),
            ("Benefit to Cost and Risk", "benefit_cost_risk_value"),
        ]
        data: list[dict[str, Any]] = []
        for metric_label, key in metrics:
            row: dict[str, Any] = {"metric": metric_label}
            for aggregate_row in self.aggregate_result_rows:
                value = aggregate_row.get(key)
                row[aggregate_row["alternative"]] = 0.0 if value is None else float(value)
            data.append(row)
        return data

    @rx.var(cache=True)
    def scenario_chart_data(self) -> list[dict[str, Any]]:
        normalized_weights = normalize_scenario_weights(self._scenarios_domain())
        data: list[dict[str, Any]] = []
        for scenario in self._scenarios_domain():
            row: dict[str, Any] = {"scenario": scenario.name}
            for alternative in self._alternatives_domain():
                abs_value = calculate_abs(
                    alternative=alternative,
                    profile_id=self.active_profile_id,
                    scenario_id=scenario.id,
                    attributes=self._attributes_domain(),
                    weight_entries=self._weights_domain(),
                    scores=self._scores_domain(),
                )
                row[alternative.name] = calculate_weighted_abs(
                    abs_value,
                    normalized_weights.get(scenario.id, 0.0),
                )
            data.append(row)
        return data

    @rx.var(cache=True)
    def radar_chart_data(self) -> list[dict[str, Any]]:
        scores = self._scores_domain()
        data: list[dict[str, Any]] = []
        for attribute in self.attributes:
            row: dict[str, Any] = {"attribute": attribute["name"]}
            for alternative in self.alternatives:
                row[alternative["name"]] = get_score(
                    scores,
                    self.active_profile_id,
                    self.active_scenario_id,
                    alternative["id"],
                    default=_DEFAULT_SCORE,
                )
            data.append(row)
        return data


def status_banner() -> rx.Component:
    return rx.box(
        rx.text(TradeoffState.status_message, size="3", font_weight="600"),
        background="rgba(15,118,110,0.10)",
        color="#0f4f4a",
        border="1px solid rgba(15,118,110,0.18)",
        border_radius="16px",
        padding="0.9rem 1rem",
    )


def project_panel() -> rx.Component:
    return panel(
        "Study Context",
        "Update the current study metadata and persistence controls.",
        rx.form(
            rx.vstack(
                rx.hstack(
                    rx.text("Current saved study:", size="2", color=TEXT_MUTED),
                    rx.text(TradeoffState.current_study_name, size="2", color=TEXT_STRONG, font_weight="600"),
                    spacing="2",
                    align="center",
                ),
                rx.input(
                    name="project_name",
                    default_value=TradeoffState.project_name,
                    placeholder="Study name",
                    size="3",
                ),
                rx.text_area(
                    name="project_description",
                    default_value=TradeoffState.project_description,
                    placeholder="Describe the study context",
                    min_height="8rem",
                ),
                rx.hstack(
                    rx.button("Save context", type="submit", color_scheme="teal"),
                    rx.button("Save study", type="button", variant="soft", on_click=TradeoffState.save_now),
                    rx.button("Reload current study", type="button", variant="soft", color_scheme="orange", on_click=TradeoffState.reload_saved_state),
                    rx.button("New study", type="button", variant="soft", color_scheme="blue", on_click=TradeoffState.create_new_study),
                    rx.button("Restore sample", type="button", variant="soft", color_scheme="gray", on_click=TradeoffState.reset_demo),
                    spacing="3",
                    wrap="wrap",
                ),
                spacing="3",
                align_items="stretch",
            ),
            on_submit=TradeoffState.update_project,
        ),
    )


def study_library_panel() -> rx.Component:
    return panel(
        "Saved Studies",
        "Browse all saved studies and reopen any of them later. Each saved study keeps scenarios, profiles, attributes, weights, scores, formulas, and a results snapshot.",
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Study"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell("Profiles"),
                        rx.table.column_header_cell("Scenarios"),
                        rx.table.column_header_cell("Alternatives"),
                        rx.table.column_header_cell("Last saved"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.study_library_rows,
                        lambda study: rx.table.row(
                            rx.table.row_header_cell(
                                rx.button(
                                    rx.hstack(
                                        rx.text(study["name"], font_weight="600"),
                                        rx.cond(
                                            study["is_current"],
                                            rx.badge("Current", color_scheme="teal", variant="soft"),
                                            rx.box(),
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    variant="ghost",
                                    on_click=TradeoffState.load_study(study["id"]),
                                    justify="start",
                                    width="100%",
                                )
                            ),
                            rx.table.cell(study["description"]),
                            rx.table.cell(study["profiles"]),
                            rx.table.cell(study["scenarios"]),
                            rx.table.cell(study["alternatives"]),
                            rx.table.cell(study["updated_at"]),
                            rx.table.cell(
                                rx.button(
                                    "Select",
                                    size="1",
                                    variant="soft",
                                    on_click=TradeoffState.load_study(study["id"]),
                                )
                            ),
                            on_click=TradeoffState.load_study(study["id"]),
                            cursor="pointer",
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
    )


def profile_panel() -> rx.Component:
    return panel(
        "Profiles",
        "Profiles define named configurations of weights and scores, such as Risk Aversion or Future Proof.",
        rx.grid(
            rx.form(
                rx.vstack(
                    rx.input(name="name", placeholder="Profile name", size="3"),
                    rx.text_area(
                        name="description",
                        placeholder="What this profile represents",
                        min_height="6rem",
                    ),
                    rx.button("Add profile", type="submit", color_scheme="teal"),
                    spacing="3",
                    align_items="stretch",
                ),
                on_submit=TradeoffState.add_profile,
                reset_on_submit=True,
            ),
            rx.vstack(
                rx.text("Current analysis focus", size="2", color=TEXT_MUTED),
                record_select(
                    TradeoffState.profile_options,
                    TradeoffState.active_profile_id,
                    TradeoffState.set_active_profile,
                    "Select profile",
                ),
                align_items="stretch",
                spacing="2",
            ),
            columns="1fr 1fr",
            spacing="4",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Profile"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.profile_rows,
                        lambda profile: rx.table.row(
                            rx.table.row_header_cell(profile["name"]),
                            rx.table.cell(profile["description"]),
                            rx.table.cell(
                                rx.button(
                                    "Remove",
                                    size="1",
                                    variant="soft",
                                    color_scheme="red",
                                    on_click=TradeoffState.remove_profile(profile["id"]),
                                )
                            ),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
    )


def alternatives_panel() -> rx.Component:
    return panel(
        "Alternatives",
        "Define the trade options.",
        rx.form(
            rx.vstack(
                rx.input(name="name", placeholder="Alternative name", size="3"),
                rx.text_area(name="description", placeholder="Alternative description", min_height="6rem"),
                rx.button("Add alternative", type="submit", color_scheme="teal"),
                spacing="3",
                align_items="stretch",
            ),
            on_submit=TradeoffState.add_alternative,
            reset_on_submit=True,
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Alternative"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.alternatives,
                        lambda alternative: rx.table.row(
                            rx.table.row_header_cell(alternative["name"]),
                            rx.table.cell(alternative["description"]),
                            rx.table.cell(
                                rx.button(
                                    "Remove",
                                    size="1",
                                    variant="soft",
                                    color_scheme="red",
                                    on_click=TradeoffState.remove_alternative(alternative["id"]),
                                )
                            ),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
    )


def attributes_panel() -> rx.Component:
    return panel(
        "Attributes",
        "Define the quality attributes used in the trade study.",
        rx.form(
            rx.vstack(
                rx.input(name="name", placeholder="Attribute name", size="3"),
                rx.text_area(name="description", placeholder="Attribute description", min_height="6rem"),
                rx.button("Add attribute", type="submit", color_scheme="teal"),
                spacing="3",
                align_items="stretch",
            ),
            on_submit=TradeoffState.add_attribute,
            reset_on_submit=True,
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Attribute"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.attributes,
                        lambda attribute: rx.table.row(
                            rx.table.row_header_cell(attribute["name"]),
                            rx.table.cell(attribute["description"]),
                            rx.table.cell(
                                rx.button(
                                    "Remove",
                                    size="1",
                                    variant="soft",
                                    color_scheme="red",
                                    on_click=TradeoffState.remove_attribute(attribute["id"]),
                                )
                            ),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
    )


def scenarios_panel() -> rx.Component:
    return panel(
        "Scenarios",
        "Scenarios contribute to the aggregated result through their scenario weights.",
        rx.form(
            rx.vstack(
                rx.input(name="name", placeholder="Scenario name", size="3"),
                rx.input(
                    name="weight",
                    placeholder="Scenario weight (0 to 1)",
                    type="text",
                    input_mode="decimal",
                    size="3",
                ),
                rx.text_area(name="description", placeholder="Scenario description", min_height="6rem"),
                rx.button("Add scenario", type="submit", color_scheme="teal"),
                spacing="3",
                align_items="stretch",
            ),
            on_submit=TradeoffState.add_scenario,
            reset_on_submit=True,
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Scenario"),
                        rx.table.column_header_cell("Weight"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.scenario_rows,
                        lambda scenario: rx.table.row(
                            rx.table.row_header_cell(scenario["name"]),
                            rx.table.cell(
                                rx.form(
                                    rx.hstack(
                                        rx.input(name="scenario_id", type="hidden", value=scenario["id"]),
                                        rx.input(
                                            name="weight",
                                            type="text",
                                            input_mode="decimal",
                                            default_value=scenario["weight"],
                                            width="8rem",
                                            min_width="8rem",
                                        ),
                                        rx.button("Save", type="submit", size="1"),
                                        spacing="2",
                                        align="center",
                                        wrap="nowrap",
                                    ),
                                    on_submit=TradeoffState.save_scenario_weight,
                                    width="100%",
                                )
                            ),
                            rx.table.cell(scenario["description"]),
                            rx.table.cell(
                                rx.button(
                                    "Remove",
                                    size="1",
                                    variant="soft",
                                    color_scheme="red",
                                    on_click=TradeoffState.remove_scenario(scenario["id"]),
                                )
                            ),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
    )


def weight_matrix_panel() -> rx.Component:
    return panel(
        "Profile Weight Matrix",
        "For the selected profile and scenario, configure the attribute and local weights of every attribute. Global weight is calculated as Attribute Weight times Local Weight.",
        rx.grid(
            rx.vstack(
                rx.text("Profile", size="2", color=TEXT_MUTED),
                record_select(
                    TradeoffState.profile_options,
                    TradeoffState.active_profile_id,
                    TradeoffState.set_active_profile,
                    "Select profile",
                ),
                spacing="2",
                align_items="stretch",
            ),
            rx.vstack(
                rx.text("Scenario", size="2", color=TEXT_MUTED),
                record_select(
                    TradeoffState.scenario_options,
                    TradeoffState.active_scenario_id,
                    TradeoffState.set_active_scenario,
                    "Select scenario",
                ),
                spacing="2",
                align_items="stretch",
            ),
            columns="1fr 1fr",
            spacing="4",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Attribute"),
                        rx.table.column_header_cell("Attribute Weight"),
                        rx.table.column_header_cell("Local Weight"),
                        rx.table.column_header_cell("Global weight"),
                        rx.table.column_header_cell("Description"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.weight_matrix_rows,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["attribute"]),
                            rx.table.cell(
                                rx.input(
                                    value=row["attribute_weight"],
                                    on_change=TradeoffState.set_draft_attribute_weight(row["id"]),
                                    type="text",
                                    input_mode="decimal",
                                    width="8rem",
                                    min_width="8rem",
                                )
                            ),
                            rx.table.cell(
                                rx.input(
                                    value=row["local_weight"],
                                    on_change=TradeoffState.set_draft_local_weight(row["id"]),
                                    type="text",
                                    input_mode="decimal",
                                    width="8rem",
                                    min_width="8rem",
                                )
                            ),
                            rx.table.cell(row["global_weight"]),
                            rx.table.cell(row["description"]),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
        rx.hstack(
            rx.spacer(),
            rx.button(
                "Save all attribute weights",
                color_scheme="teal",
                on_click=TradeoffState.save_all_weight_rows,
            ),
            width="100%",
        ),
    )


def score_matrix_panel() -> rx.Component:
    return panel(
        "Profile Score Matrix",
        "For the selected profile, configure the 1-to-5 qualitative score of every alternative across all scenarios.",
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Alternative"),
                        rx.table.column_header_cell("Scenario"),
                        rx.table.column_header_cell("Score"),
                        rx.table.column_header_cell("Current"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.score_matrix_rows,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["alternative_name"]),
                            rx.table.cell(row["scenario_name"]),
                            rx.table.cell(
                                rx.input(
                                    value=row["score"],
                                    on_change=TradeoffState.set_draft_score(
                                        row["scenario_id"],
                                        row["alternative_id"],
                                    ),
                                    type="text",
                                    input_mode="numeric",
                                    width="7rem",
                                    min_width="7rem",
                                )
                            ),
                            rx.table.cell(row["score_display"]),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
        rx.hstack(
            rx.spacer(),
            rx.button(
                "Save all scenario scores",
                color_scheme="teal",
                on_click=TradeoffState.save_all_scores,
            ),
            width="100%",
        ),
    )


def benefit_cost_risk_panel() -> rx.Component:
    return panel(
        "Benefit to Cost and Risk Model",
        "For the selected profile, configure alpha and beta where alpha + beta = 1, plus a cost score and risk score from 1 to 5 for each alternative.",
        rx.grid(
            rx.vstack(
                rx.text("Profile", size="2", color=TEXT_MUTED),
                record_select(
                    TradeoffState.profile_options,
                    TradeoffState.active_profile_id,
                    TradeoffState.set_active_profile,
                    "Select profile",
                ),
                spacing="2",
                align_items="stretch",
            ),
            rx.vstack(
                rx.text("Alpha (cost weight)", size="2", color=TEXT_MUTED),
                rx.input(
                    value=TradeoffState.benefit_cost_risk_weight_row["alpha"],
                    on_change=TradeoffState.set_alpha,
                    type="text",
                    input_mode="decimal",
                    width="8rem",
                ),
                spacing="2",
                align_items="stretch",
            ),
            rx.vstack(
                rx.text("Beta (risk weight)", size="2", color=TEXT_MUTED),
                rx.input(
                    value=TradeoffState.benefit_cost_risk_weight_row["beta"],
                    on_change=TradeoffState.set_beta,
                    type="text",
                    input_mode="decimal",
                    width="8rem",
                ),
                spacing="2",
                align_items="stretch",
            ),
            columns="1.4fr 1fr 1fr",
            spacing="4",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Alternative"),
                        rx.table.column_header_cell("Cost score"),
                        rx.table.column_header_cell("Risk score"),
                        rx.table.column_header_cell("Current cost"),
                        rx.table.column_header_cell("Current risk"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.benefit_cost_risk_score_rows,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["alternative_name"]),
                            rx.table.cell(
                                rx.input(
                                    value=row["cost_score"],
                                    on_change=TradeoffState.set_draft_cost_score(row["alternative_id"]),
                                    type="text",
                                    input_mode="numeric",
                                    width="7rem",
                                    min_width="7rem",
                                )
                            ),
                            rx.table.cell(
                                rx.input(
                                    value=row["risk_score"],
                                    on_change=TradeoffState.set_draft_risk_score(row["alternative_id"]),
                                    type="text",
                                    input_mode="numeric",
                                    width="7rem",
                                    min_width="7rem",
                                )
                            ),
                            rx.table.cell(row["cost_score_display"]),
                            rx.table.cell(row["risk_score_display"]),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
        rx.hstack(
            rx.spacer(),
            rx.button(
                "Save cost and risk scores",
                color_scheme="teal",
                on_click=TradeoffState.save_all_cost_risk_scores,
            ),
            width="100%",
        ),
    )


def break_even_panel() -> rx.Component:
    return panel(
        "Break-Even Cost Model",
        "Model TCO as Initial cost plus Number of integrations times Integration cost. Configure the global change rate and horizon, then set the cost inputs for each alternative.",
        rx.grid(
            rx.vstack(
                rx.text("Integrations per year", size="2", color=TEXT_MUTED),
                rx.input(
                    value=TradeoffState.break_even_model_row["integrations_per_year"],
                    on_change=TradeoffState.set_draft_integrations_per_year,
                    type="text",
                    input_mode="decimal",
                    width="10rem",
                ),
                spacing="2",
                align_items="stretch",
            ),
            rx.vstack(
                rx.text("Years", size="2", color=TEXT_MUTED),
                rx.input(
                    value=TradeoffState.break_even_model_row["years"],
                    on_change=TradeoffState.set_draft_years,
                    type="text",
                    input_mode="decimal",
                    width="10rem",
                ),
                spacing="2",
                align_items="stretch",
            ),
            rx.vstack(
                rx.text("Modeled integrations", size="2", color=TEXT_MUTED),
                rx.text(
                    TradeoffState.break_even_model_row["total_integrations"],
                    size="6",
                    font_weight="700",
                    color=TEXT_STRONG,
                ),
                spacing="2",
                align_items="stretch",
            ),
            columns="1fr 1fr 1fr",
            spacing="4",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Alternative"),
                        rx.table.column_header_cell("Initial cost"),
                        rx.table.column_header_cell("Integration cost"),
                        rx.table.column_header_cell("TCO at modeled horizon"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        TradeoffState.break_even_cost_rows,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["alternative_name"]),
                            rx.table.cell(
                                rx.input(
                                    value=row["initial_cost"],
                                    on_change=TradeoffState.set_draft_initial_cost(row["alternative_id"]),
                                    type="text",
                                    input_mode="decimal",
                                    width="8rem",
                                    min_width="8rem",
                                )
                            ),
                            rx.table.cell(
                                rx.input(
                                    value=row["integration_cost"],
                                    on_change=TradeoffState.set_draft_integration_cost(row["alternative_id"]),
                                    type="text",
                                    input_mode="decimal",
                                    width="8rem",
                                    min_width="8rem",
                                )
                            ),
                            rx.table.cell(row["tco_display"]),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            overflow_x="auto",
        ),
        rx.hstack(
            rx.spacer(),
            rx.button(
                "Save break-even model",
                color_scheme="teal",
                on_click=TradeoffState.save_break_even_model,
            ),
            width="100%",
        ),
    )


def formula_lab_tab() -> rx.Component:
    return rx.vstack(
        panel(
            "Formula Builder",
            "Create restricted LaTeX-like formulas and insert tokens from the variable catalog. You can use wildcard summations such as \\sum_{global_weight_*} and indexed summations such as \\sum_{i=1}^{num_scenarios}(weighted_abs_i).",
            rx.grid(
                rx.vstack(
                    rx.cond(
                        TradeoffState.is_editing_formula,
                        rx.text("Editing saved formula", color=TEXT_MUTED, size="2"),
                        rx.text("Creating new formula", color=TEXT_MUTED, size="2"),
                    ),
                    rx.input(value=TradeoffState.draft_formula_name, on_change=TradeoffState.set_draft_formula_name, placeholder="Formula name", size="3"),
                    rx.text_area(value=TradeoffState.draft_formula_description, on_change=TradeoffState.set_draft_formula_description, placeholder="Formula description", min_height="6rem"),
                    rx.text_area(value=TradeoffState.draft_formula_latex, on_change=TradeoffState.set_draft_formula_latex, placeholder=r"Example: \sum_{i=1}^{num_scenarios}(global_weight_i \cdot score_i)", min_height="8rem"),
                    rx.hstack(
                        rx.button("+", variant="soft", on_click=TradeoffState.append_formula_token("+")),
                        rx.button("-", variant="soft", on_click=TradeoffState.append_formula_token("-")),
                        rx.button(r"\cdot", variant="soft", on_click=TradeoffState.append_formula_token(r"\cdot")),
                        rx.button(r"\frac{}{ }", variant="soft", on_click=TradeoffState.append_formula_token(r"\frac{}{ }")),
                        rx.button(r"\sum_{}", variant="soft", on_click=TradeoffState.append_formula_token(r"\sum_{}")),
                        rx.button(r"\sum_{i=1}^{num_scenarios}()", variant="soft", on_click=TradeoffState.append_formula_token(r"\sum_{i=1}^{num_scenarios}()")),
                        rx.button("( )", variant="soft", on_click=TradeoffState.append_formula_token("( )")),
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.cond(
                            TradeoffState.is_editing_formula,
                            rx.button("Update formula", color_scheme="teal", on_click=TradeoffState.save_formula),
                            rx.button("Add formula", color_scheme="teal", on_click=TradeoffState.save_formula),
                        ),
                        rx.button("Clear", variant="soft", on_click=TradeoffState.clear_formula_builder),
                        spacing="3",
                    ),
                    spacing="3",
                    align_items="stretch",
                    width="100%",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Token"),
                                rx.table.column_header_cell("Meaning"),
                                rx.table.column_header_cell(""),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                TradeoffState.formula_variable_catalog,
                                lambda item: rx.table.row(
                                    rx.table.row_header_cell(
                                        item["token"],
                                        max_width="15rem",
                                        white_space="normal",
                                        word_break="break-word",
                                    ),
                                    rx.table.cell(
                                        item["label"],
                                        max_width="16rem",
                                        white_space="normal",
                                    ),
                                    rx.table.cell(
                                        rx.button(
                                            "Insert",
                                            size="1",
                                            variant="soft",
                                            on_click=TradeoffState.append_formula_token(item["token"]),
                                        ),
                                        width="7rem",
                                    ),
                                ),
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    max_height="28rem",
                    overflow_y="auto",
                    overflow_x="auto",
                    width="100%",
                ),
                columns="minmax(0, 1.2fr) minmax(32rem, 1.05fr)",
                spacing="4",
                width="100%",
                align_items="start",
            ),
        ),
        panel(
            "Registered Formulas",
            "Built-in formulas are protected. Disabled formulas stay registered but are excluded from results.",
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Formula"),
                            rx.table.column_header_cell("LaTeX"),
                            rx.table.column_header_cell("Description"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell(""),
                            rx.table.column_header_cell(""),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            TradeoffState.registered_formula_rows,
                            lambda formula: rx.table.row(
                                rx.table.row_header_cell(formula["name"]),
                                rx.table.cell(formula["latex"]),
                                rx.table.cell(formula["description"]),
                                rx.table.cell(
                                    rx.badge(
                                        rx.cond(formula["enabled"], "Enabled", "Disabled"),
                                        color_scheme=rx.cond(formula["enabled"], "teal", "gray"),
                                        variant="soft",
                                    )
                                ),
                                rx.table.cell(
                                    rx.button(
                                        rx.cond(formula["enabled"], "Disable", "Enable"),
                                        size="1",
                                        variant="soft",
                                        color_scheme=rx.cond(formula["enabled"], "orange", "teal"),
                                        on_click=TradeoffState.toggle_formula_enabled(formula["id"]),
                                    )
                                ),
                                rx.table.cell(
                                    rx.cond(
                                        formula["builtin"],
                                        rx.text("Protected", color=TEXT_MUTED),
                                        rx.button(
                                            "Edit",
                                            size="1",
                                            variant="soft",
                                            on_click=TradeoffState.start_edit_formula(formula["id"]),
                                        ),
                                    )
                                ),
                                rx.table.cell(
                                    rx.cond(
                                        formula["builtin"],
                                        rx.text("Protected", color=TEXT_MUTED),
                                        rx.button(
                                            "Remove",
                                            size="1",
                                            variant="soft",
                                            color_scheme="red",
                                            on_click=TradeoffState.remove_formula(formula["id"]),
                                        ),
                                    )
                                ),
                            ),
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
            ),
        ),
        spacing="5",
        width="100%",
    )


def results_tab() -> rx.Component:
    return rx.vstack(
        panel(
            "Results by Alternative",
            "The selected profile is applied across all scenarios. The table shows the modeled TCO and the computed benefit of each enabled formula for every alternative.",
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Alternative"),
                            rx.table.column_header_cell("TCO"),
                            rx.foreach(
                                TradeoffState.enabled_formula_columns,
                                lambda formula: rx.table.column_header_cell(formula["name"]),
                            ),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            TradeoffState.aggregate_result_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["alternative"]),
                                rx.table.cell(
                                    row["tco"],
                                    background=rx.cond(
                                        row["tco"] == TradeoffState.aggregate_tco_minimum,
                                        "#dcfce7",
                                        "transparent",
                                    ),
                                    color=rx.cond(
                                        row["tco"] == TradeoffState.aggregate_tco_minimum,
                                        "#14532d",
                                        "inherit",
                                    ),
                                    font_weight=rx.cond(
                                        row["tco"] == TradeoffState.aggregate_tco_minimum,
                                        "700",
                                        "400",
                                    ),
                                ),
                                rx.foreach(
                                    TradeoffState.enabled_formula_columns,
                                    lambda formula: rx.table.cell(
                                        row[f"formula_{formula['id']}"],
                                        background=rx.cond(
                                            row[f"formula_{formula['id']}"]
                                            == TradeoffState.aggregate_formula_maxima.get(formula["id"], ""),
                                            "#dcfce7",
                                            "transparent",
                                        ),
                                        color=rx.cond(
                                            row[f"formula_{formula['id']}"]
                                            == TradeoffState.aggregate_formula_maxima.get(formula["id"], ""),
                                            "#14532d",
                                            "inherit",
                                        ),
                                        font_weight=rx.cond(
                                            row[f"formula_{formula['id']}"]
                                            == TradeoffState.aggregate_formula_maxima.get(formula["id"], ""),
                                            "700",
                                            "400",
                                        ),
                                    ),
                                ),
                            ),
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
            ),
        ),
        panel(
            "Profile by Scenario",
            "Detailed scenario-level results for the selected profile.",
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Scenario"),
                            rx.table.column_header_cell("Alternative"),
                            rx.foreach(
                                TradeoffState.enabled_formula_columns,
                                lambda formula: rx.table.column_header_cell(formula["name"]),
                            ),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            TradeoffState.profile_scenario_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["scenario"]),
                                rx.table.cell(row["alternative"]),
                                rx.foreach(
                                    TradeoffState.enabled_formula_columns,
                                    lambda formula: rx.table.cell(row[f"formula_{formula['id']}"]),
                                ),
                            ),
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                max_height="24rem",
                overflow_y="auto",
                overflow_x="auto",
            ),
        ),
        rx.grid(
            panel(
                "Aggregate Comparison",
                "Grouped comparison by measure, with one bar per alternative inside each metric group.",
                rx.cond(
                    TradeoffState.aggregate_chart_data.length() > 0,
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.x_axis(data_key="metric"),
                        rx.recharts.y_axis(),
                        rx.recharts.tooltip(),
                        rx.recharts.legend(),
                        rx.foreach(
                            TradeoffState.series_meta,
                            lambda series: rx.recharts.bar(
                                data_key=series["name"],
                                name=series["name"],
                                fill=series["color"],
                                radius=12,
                            ),
                        ),
                        data=TradeoffState.aggregate_chart_data,
                        height=380,
                        width="100%",
                    ),
                    empty_state("No aggregate results", "Add profiles, scenarios, weights, and scores to compute results."),
                ),
            ),
            panel(
                "Scenario Distribution",
                "Scenario-weighted result of each alternative for the selected profile.",
                rx.cond(
                    TradeoffState.scenario_chart_data.length() > 0,
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.x_axis(data_key="scenario"),
                        rx.recharts.y_axis(),
                        rx.recharts.tooltip(),
                        rx.recharts.legend(),
                        rx.foreach(
                            TradeoffState.series_meta,
                            lambda series: rx.recharts.bar(
                                data_key=series["name"],
                                name=series["name"],
                                fill=series["color"],
                            ),
                        ),
                        data=TradeoffState.scenario_chart_data,
                        height=380,
                        width="100%",
                    ),
                    empty_state("No scenario comparison", "Add multiple scenarios to compare profile results."),
                ),
            ),
            columns="1fr",
            spacing="4",
            width="100%",
        ),
        panel(
            "Break-Even Results",
            "TCO curves and break-even thresholds across alternatives using the modeled number of integrations.",
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Comparison"),
                            rx.table.column_header_cell("Exact break-even (N)"),
                            rx.table.column_header_cell("First whole integration"),
                            rx.table.column_header_cell("Break-even year"),
                            rx.table.column_header_cell("Status"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            TradeoffState.break_even_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["comparison"]),
                                rx.table.cell(row["exact_break_even"]),
                                rx.table.cell(row["first_whole_integration"]),
                                rx.table.cell(row["break_even_year"]),
                                rx.table.cell(row["status"]),
                            ),
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                overflow_x="auto",
            ),
            rx.cond(
                TradeoffState.break_even_chart_data.length() > 0,
                rx.recharts.line_chart(
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.x_axis(data_key="integrations", label={"value": "Integrations", "position": "insideBottom", "offset": -4}),
                    rx.recharts.y_axis(label={"value": "TCO", "angle": -90, "position": "insideLeft"}),
                    rx.recharts.tooltip(),
                    rx.recharts.legend(),
                    rx.foreach(
                        TradeoffState.series_meta,
                        lambda series: rx.recharts.line(
                            data_key=series["name"],
                            name=series["name"],
                            stroke=series["color"],
                            stroke_width=3,
                            dot=False,
                            type="monotone",
                        ),
                    ),
                    data=TradeoffState.break_even_chart_data,
                    height=380,
                    width="100%",
                ),
                empty_state("No break-even data", "Add at least one alternative and save the break-even cost model to render the TCO chart."),
            ),
        ),
        panel(
            "Configured Variables by Trade Option",
            "Full configuration table for the selected profile across all scenarios and alternatives.",
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Scenario"),
                            rx.table.column_header_cell("Alternative"),
                            rx.table.column_header_cell("Attribute"),
                            rx.table.column_header_cell("Scenario weight"),
                            rx.table.column_header_cell("Attribute weight"),
                            rx.table.column_header_cell("Local weight"),
                            rx.table.column_header_cell("Global weight"),
                            rx.table.column_header_cell("Score"),
                            rx.table.column_header_cell("Contribution"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            TradeoffState.configured_variable_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["scenario"]),
                                rx.table.cell(row["alternative"]),
                                rx.table.cell(row["attribute"]),
                                rx.table.cell(row["scenario_weight"]),
                                rx.table.cell(row["attribute_weight"]),
                                rx.table.cell(row["local_weight"]),
                                rx.table.cell(row["global_weight"]),
                                rx.table.cell(row["score"]),
                                rx.table.cell(row["contribution"]),
                            ),
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                max_height="32rem",
                overflow_y="auto",
                overflow_x="auto",
            ),
        ),
        spacing="5",
        width="100%",
    )


def overview_tab() -> rx.Component:
    return rx.vstack(
        rx.grid(
            stat_card("Saved Studies", TradeoffState.study_library.length().to_string(), "Full studies available in the shared JSON library.", accent="#0f766e"),
            stat_card("Profiles", TradeoffState.profiles.length().to_string(), "Named analysis lenses such as Risk Aversion or Future Proof.", accent="#0f766e"),
            stat_card("Alternatives", TradeoffState.alternatives.length().to_string(), "Trade options currently modeled.", accent="#b45309"),
            stat_card("Attributes", TradeoffState.attributes.length().to_string(), "Qualitative dimensions of comparison.", accent="#1d4ed8"),
            stat_card("Current Analysis Focus", TradeoffState.selected_profile_name, "All result aggregates are computed from this selected profile.", accent="#be123c"),
            columns="repeat(5, minmax(0, 1fr))",
            spacing="4",
            width="100%",
        ),
        project_panel(),
        study_library_panel(),
        profile_panel(),
        spacing="5",
        width="100%",
    )


def instructions_tab() -> rx.Component:
    return rx.vstack(
        panel(
            "How to Run a Trade-Off Analysis",
            "Follow this workflow to build a study from scratch and interpret the results with a simple hypothetical example.",
            rx.vstack(
                rx.box(
                    rx.heading("1. Define the study context", size="5", color=TEXT_STRONG),
                    rx.text(
                        "Start in Overview. Give the study a clear name and a short description of the decision you need to support.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Example: compare two deployment strategies for a software platform that must evolve over time while keeping control over cost and operational risk.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("2. Create the decision profiles", size="5", color=TEXT_STRONG),
                    rx.text(
                        "Add one or more profiles that represent different decision lenses, such as Risk Aversion, Future Proof, or Cost Sensitivity.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Each profile lets you configure different attribute weights, local weights, scores, and cost-risk parameters.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("3. Model the trade alternatives", size="5", color=TEXT_STRONG),
                    rx.text(
                        "In Modeling > Alternatives, add the options you want to compare. Keep the names short and descriptive.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Example alternatives: Managed Platform and Self-Managed Stack.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("4. Add attributes and scenarios", size="5", color=TEXT_STRONG),
                    rx.text(
                        "Add the quality attributes that matter for the decision, then define the scenarios that represent the situations you want to test.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Example attributes: Evolvability, Time to Field, Operability, and Sovereignty. Example scenarios: Capability Growth, Rapid Delivery, and Restricted Deployment.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("5. Configure weights and scores", size="5", color=TEXT_STRONG),
                    rx.text(
                        "For each profile and scenario, set Attribute Weight and Local Weight in the Profile Weight Matrix. Then set the 1-to-5 scores of each alternative in the Profile Score Matrix.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Use scenario weights to indicate how important each scenario is in the final aggregate analysis.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("6. Add cost and break-even models", size="5", color=TEXT_STRONG),
                    rx.text(
                        "Use Benefit to Cost and Risk Model to define alpha, beta, cost score, and risk score. Use Break-Even Cost Model to define initial cost, integration cost, integrations per year, and project lifetime.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "This lets you compare benefit, benefit-to-cost-and-risk, and long-term total cost of ownership in the same study.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("7. Build or reuse formulas", size="5", color=TEXT_STRONG),
                    rx.text(
                        "In Formula Lab, use the Formula Builder to create LaTeX-like formulas with built-in variables, wildcard summations, or indexed summations.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "Enable only the formulas you want to include in the final result tables and charts.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.heading("8. Read the results", size="5", color=TEXT_STRONG),
                    rx.text(
                        "Open Results to compare alternatives by formula, inspect scenario-by-scenario outcomes, review aggregate charts, and study break-even thresholds.",
                        color=TEXT_MUTED,
                    ),
                    rx.text(
                        "A good practice is to check whether the same alternative remains strong across multiple profiles and scenarios before making a recommendation.",
                        color=TEXT_MUTED,
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
        ),
        panel(
            "Hypothetical Example",
            "This example shows how a team might use the tool to compare two architectural options.",
            rx.box(
                rx.text(
                    "Study: ANALYSIS Deployment Decision",
                    font_weight="700",
                    color=TEXT_STRONG,
                ),
                rx.text(
                    "Alternatives: Managed Platform and Self-Managed Stack.",
                    color=TEXT_MUTED,
                ),
                rx.text(
                    "Profile: Future Proof. Scenarios: Capability Growth, Fast Delivery, Controlled Operations.",
                    color=TEXT_MUTED,
                ),
                rx.text(
                    "Attributes: Evolvability, Operability, Time to Field, Operational Control.",
                    color=TEXT_MUTED,
                ),
                rx.text(
                    "Interpretation: the Managed Platform might score higher on Benefit(A) in fast-delivery scenarios, while the Self-Managed Stack might perform better in control-heavy scenarios. The break-even model can then show whether the initially more expensive option becomes cheaper after enough integrations over the product lifetime.",
                    color=TEXT_MUTED,
                ),
                rx.text(
                    "Decision logic: if one option delivers stronger aggregate benefit and an acceptable long-term TCO under the most relevant profile, it becomes the preferred recommendation.",
                    color=TEXT_MUTED,
                ),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="5",
        width="100%",
    )


def modeling_tab() -> rx.Component:
    return rx.vstack(
        alternatives_panel(),
        attributes_panel(),
        scenarios_panel(),
        weight_matrix_panel(),
        score_matrix_panel(),
        benefit_cost_risk_panel(),
        break_even_panel(),
        spacing="5",
        width="100%",
    )


def index() -> rx.Component:
    return rx.box(
        rx.box(
            position="fixed",
            inset="0",
            background=(
                "radial-gradient(circle at top left, rgba(15,118,110,0.20), transparent 28%), "
                "radial-gradient(circle at top right, rgba(180,83,9,0.14), transparent 25%), "
                "linear-gradient(180deg, #eff6f3 0%, #f8fbfb 42%, #eef3f2 100%)"
            ),
            z_index="-1",
        ),
        rx.container(
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.text(
                            "TRADA Studio (Trade-Off Analysis Studio)",
                            size="2",
                            letter_spacing="0.14em",
                            text_transform="uppercase",
                            color="#0f766e",
                            font_weight="700",
                        ),
                        rx.heading(
                            TradeoffState.project_name,
                            size="9",
                            font_family=FONT_DISPLAY,
                            color=TEXT_STRONG,
                            line_height="1.05",
                        ),
                        rx.text(
                            TradeoffState.project_description,
                            size="4",
                            color=TEXT_MUTED,
                            max_width="58rem",
                            line_height="1.7",
                        ),
                        spacing="4",
                        align_items="start",
                    ),
                    padding_top="3rem",
                ),
                status_banner(),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Overview", value="overview"),
                        rx.tabs.trigger("Instructions", value="instructions"),
                        rx.tabs.trigger("Modeling", value="modeling"),
                        rx.tabs.trigger("Formula Lab", value="formula_lab"),
                        rx.tabs.trigger("Results", value="results"),
                    ),
                    rx.tabs.content(overview_tab(), value="overview"),
                    rx.tabs.content(instructions_tab(), value="instructions"),
                    rx.tabs.content(modeling_tab(), value="modeling"),
                    rx.tabs.content(formula_lab_tab(), value="formula_lab"),
                    rx.tabs.content(results_tab(), value="results"),
                    default_value="overview",
                    width="100%",
                ),
                spacing="5",
                align_items="stretch",
                padding_bottom="4rem",
            ),
            max_width="116rem",
            width="100%",
            padding_x="1.75rem",
        ),
        min_height="100vh",
        font_family=FONT_BODY,
        color=TEXT_STRONG,
        background=SURFACE,
    )


app = rx.App(
    theme=rx.theme(accent_color="teal", radius="large"),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap",
    ],
    style={"font_family": FONT_BODY},
)
app.add_page(index, title="TRADA Studio (Trade-Off Analysis Studio)", on_load=TradeoffState.load_saved_state)
