"""Editable seed data used to initialize the application."""

from __future__ import annotations

import copy
from typing import Any


SAMPLE_DATA: dict[str, Any] = {
    "project_name": "ANALYSIS Software Trade-Off",
    "project_description": (
        "Editable baseline to compare architecture options across scenarios and reusable analysis profiles."
    ),
    "alternatives": [
        {
            "id": "alt_paas",
            "name": "PaaS",
            "description": "Platform-centric option with managed runtime capabilities.",
        },
        {
            "id": "alt_non_paas",
            "name": "No PaaS",
            "description": "Self-managed stack with tighter operational control.",
        },
    ],
    "attributes": [
        {"id": "attr_evolvability", "name": "Evolvability", "description": "Ease of extension and change over time."},
        {"id": "attr_time_to_field", "name": "Time to Field", "description": "Ability to deliver capability quickly."},
        {"id": "attr_certification_fit", "name": "Certification Fit", "description": "Alignment with DAL-E evidence and certification activities."},
        {"id": "attr_operability", "name": "Operability", "description": "Supportability, observability, and operational resilience."},
        {"id": "attr_sovereignty", "name": "Sovereignty", "description": "Control over deployment, runtime, and restricted environments."},
    ],
    "scenarios": [
        {"id": "scenario_growth", "name": "Capability Growth", "description": "Frequent feature evolution and adaptation.", "weight": 0.35},
        {"id": "scenario_delivery", "name": "Rapid Delivery", "description": "Compressed delivery timeline and pressure on speed.", "weight": 0.25},
        {"id": "scenario_sovereign", "name": "Sovereign Operations", "description": "Control, certification rigor, and deployment sovereignty.", "weight": 0.40},
    ],
    "profiles": [
        {
            "id": "profile_risk_averse",
            "name": "Risk Aversion",
            "description": "Favors control, certification fit, and operational predictability.",
        },
        {
            "id": "profile_future_proof",
            "name": "Future Proof",
            "description": "Favors evolvability, fast capability growth, and long-term adaptability.",
        },
    ],
    "benefit_cost_risk_weights": [
        {"profile_id": "profile_risk_averse", "alpha": 0.45, "beta": 0.55},
        {"profile_id": "profile_future_proof", "alpha": 0.60, "beta": 0.40},
    ],
    "benefit_cost_risk_scores": [
        {"profile_id": "profile_risk_averse", "alternative_id": "alt_paas", "cost_score": 3.0, "risk_score": 4.0},
        {"profile_id": "profile_risk_averse", "alternative_id": "alt_non_paas", "cost_score": 4.0, "risk_score": 2.0},
        {"profile_id": "profile_future_proof", "alternative_id": "alt_paas", "cost_score": 3.0, "risk_score": 4.0},
        {"profile_id": "profile_future_proof", "alternative_id": "alt_non_paas", "cost_score": 4.0, "risk_score": 2.0},
    ],
    "break_even_settings": {
        "integrations_per_year": 2.0,
        "years": 20.0,
    },
    "break_even_costs": [
        {"alternative_id": "alt_paas", "initial_cost": 9.0, "integration_cost": 3.0},
        {"alternative_id": "alt_non_paas", "initial_cost": 2.0, "integration_cost": 8.0},
    ],
    "weights": [
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "attribute_id": "attr_evolvability", "global_weight": 0.55, "local_weight": 0.60},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "attribute_id": "attr_time_to_field", "global_weight": 0.45, "local_weight": 0.45},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "attribute_id": "attr_certification_fit", "global_weight": 0.90, "local_weight": 0.80},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "attribute_id": "attr_operability", "global_weight": 0.75, "local_weight": 0.70},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "attribute_id": "attr_sovereignty", "global_weight": 0.85, "local_weight": 0.75},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "attribute_id": "attr_evolvability", "global_weight": 0.45, "local_weight": 0.45},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "attribute_id": "attr_time_to_field", "global_weight": 0.50, "local_weight": 0.55},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "attribute_id": "attr_certification_fit", "global_weight": 0.85, "local_weight": 0.75},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "attribute_id": "attr_operability", "global_weight": 0.75, "local_weight": 0.70},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "attribute_id": "attr_sovereignty", "global_weight": 0.80, "local_weight": 0.70},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "attribute_id": "attr_evolvability", "global_weight": 0.40, "local_weight": 0.45},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "attribute_id": "attr_time_to_field", "global_weight": 0.35, "local_weight": 0.40},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "attribute_id": "attr_certification_fit", "global_weight": 0.98, "local_weight": 0.95},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "attribute_id": "attr_operability", "global_weight": 0.80, "local_weight": 0.80},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "attribute_id": "attr_sovereignty", "global_weight": 1.00, "local_weight": 0.98},

        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "attribute_id": "attr_evolvability", "global_weight": 0.98, "local_weight": 0.95},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "attribute_id": "attr_time_to_field", "global_weight": 0.75, "local_weight": 0.70},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "attribute_id": "attr_certification_fit", "global_weight": 0.45, "local_weight": 0.50},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "attribute_id": "attr_operability", "global_weight": 0.70, "local_weight": 0.65},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "attribute_id": "attr_sovereignty", "global_weight": 0.50, "local_weight": 0.55},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "attribute_id": "attr_evolvability", "global_weight": 0.85, "local_weight": 0.80},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "attribute_id": "attr_time_to_field", "global_weight": 0.92, "local_weight": 0.90},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "attribute_id": "attr_certification_fit", "global_weight": 0.40, "local_weight": 0.45},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "attribute_id": "attr_operability", "global_weight": 0.72, "local_weight": 0.70},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "attribute_id": "attr_sovereignty", "global_weight": 0.42, "local_weight": 0.45},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "attribute_id": "attr_evolvability", "global_weight": 0.70, "local_weight": 0.70},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "attribute_id": "attr_time_to_field", "global_weight": 0.50, "local_weight": 0.50},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "attribute_id": "attr_certification_fit", "global_weight": 0.65, "local_weight": 0.70},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "attribute_id": "attr_operability", "global_weight": 0.72, "local_weight": 0.75},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "attribute_id": "attr_sovereignty", "global_weight": 0.58, "local_weight": 0.65},
    ],
    "scores": [
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 5.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_risk_averse", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},

        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_growth", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_delivery", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_evolvability", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_time_to_field", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_certification_fit", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_operability", "score": 4.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_paas", "attribute_id": "attr_sovereignty", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_evolvability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_time_to_field", "score": 2.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_certification_fit", "score": 5.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_operability", "score": 3.0},
        {"profile_id": "profile_future_proof", "scenario_id": "scenario_sovereign", "alternative_id": "alt_non_paas", "attribute_id": "attr_sovereignty", "score": 5.0},
    ],
    "formulas": [
        {"id": "formula_benefit_cost_risk", "name": "Benefit to Cost and Risk", "latex": r"\frac{Benefit(A)}{\left(alpha \cdot cost_score(A)\right) + \left(beta \cdot risk_score(A)\right)}", "description": "Benefit(A) divided by the weighted sum of cost and risk.", "builtin": True},
    ],
    "active_profile_id": "profile_risk_averse",
    "active_scenario_id": "scenario_growth",
    "active_attribute_id": "attr_evolvability",
}


def clone_sample_data() -> dict[str, Any]:
    return copy.deepcopy(SAMPLE_DATA)


def blank_study_data() -> dict[str, Any]:
    """Create a blank study with built-in formulas only."""

    return {
        "project_name": "Untitled Trade Study",
        "project_description": "",
        "alternatives": [],
        "attributes": [],
        "scenarios": [],
        "profiles": [],
        "benefit_cost_risk_weights": [],
        "benefit_cost_risk_scores": [],
        "break_even_settings": {
            "integrations_per_year": 1.0,
            "years": 5.0,
        },
        "break_even_costs": [],
        "weights": [],
        "scores": [],
        "formulas": copy.deepcopy(SAMPLE_DATA["formulas"]),
        "active_profile_id": "",
        "active_scenario_id": "",
        "active_attribute_id": "",
    }
