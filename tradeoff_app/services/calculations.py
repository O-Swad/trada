"""Calculation services for trade-off metrics and LaTeX-like formulas."""

from __future__ import annotations

import ast
import operator
import re
from collections.abc import Mapping

from tradeoff_app.domain.models import (
    Alternative,
    Attribute,
    Formula,
    Scenario,
    ScoreEntry,
    WeightEntry,
)


_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def slugify_identifier(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "attribute"


def normalize_scenario_weights(scenarios: list[Scenario]) -> dict[str, float]:
    total = sum(max(scenario.weight, 0.0) for scenario in scenarios)
    if total <= 0:
        if not scenarios:
            return {}
        even_weight = 1.0 / len(scenarios)
        return {scenario.id: even_weight for scenario in scenarios}
    return {scenario.id: max(scenario.weight, 0.0) / total for scenario in scenarios}


def get_weight_entry(
    weight_entries: list[WeightEntry],
    profile_id: str,
    scenario_id: str,
    attribute_id: str,
) -> WeightEntry:
    for entry in weight_entries:
        if (
            entry.profile_id == profile_id
            and entry.scenario_id == scenario_id
            and entry.attribute_id == attribute_id
        ):
            return entry
    return WeightEntry(
        profile_id=profile_id,
        scenario_id=scenario_id,
        attribute_id=attribute_id,
        global_weight=0.0,
        local_weight=0.0,
    )


def get_score(
    scores: list[ScoreEntry],
    profile_id: str,
    scenario_id: str,
    alternative_id: str,
    default: float = 0.0,
) -> float:
    for score in scores:
        if (
            score.profile_id == profile_id
            and score.scenario_id == scenario_id
            and score.alternative_id == alternative_id
        ):
            return score.score
    return default


def effective_weight(entry: WeightEntry) -> float:
    return round(entry.global_weight * entry.local_weight, 6)


def attribute_contribution(entry: WeightEntry, score: float) -> float:
    return round(effective_weight(entry) * score, 6)


def calculate_abs(
    alternative: Alternative,
    profile_id: str,
    scenario_id: str,
    attributes: list[Attribute],
    weight_entries: list[WeightEntry],
    scores: list[ScoreEntry],
    global_weight_overrides: Mapping[str, float] | None = None,
) -> float:
    total = 0.0
    overrides = global_weight_overrides or {}
    for attribute in attributes:
        entry = get_weight_entry(weight_entries, profile_id, scenario_id, attribute.id)
        if attribute.id in overrides:
            entry = WeightEntry(
                profile_id=entry.profile_id,
                scenario_id=entry.scenario_id,
                attribute_id=entry.attribute_id,
                global_weight=overrides[attribute.id],
                local_weight=entry.local_weight,
            )
        score = get_score(
            scores,
            profile_id,
            scenario_id,
            alternative.id,
        )
        total += attribute_contribution(entry, score)
    return round(total, 4)


def calculate_weighted_abs(abs_value: float, normalized_scenario_weight: float) -> float:
    return round(abs_value * normalized_scenario_weight, 4)


def build_formula_context(
    alternative: Alternative,
    profile_id: str,
    scenario: Scenario,
    scenarios: list[Scenario],
    normalized_scenario_weight: float,
    normalized_scenario_weights: Mapping[str, float],
    attributes: list[Attribute],
    weight_entries: list[WeightEntry],
    scores: list[ScoreEntry],
    alpha: float,
    beta: float,
    cost_score: float,
    risk_score: float,
    abs_value: float,
) -> dict[str, float]:
    context: dict[str, float] = {
        "abs": abs_value,
        "benefit_a": abs_value,
        "num_scenarios": float(len(scenarios)),
        "alpha": alpha,
        "beta": beta,
        "cost_score": cost_score,
        "cost_score_a": cost_score,
        "risk_score": risk_score,
        "risk_score_a": risk_score,
        "scenario_weight": scenario.weight,
        "normalized_scenario_weight": normalized_scenario_weight,
        "weighted_abs": calculate_weighted_abs(abs_value, normalized_scenario_weight),
    }
    for attribute in attributes:
        slug = slugify_identifier(attribute.name)
        entry = get_weight_entry(weight_entries, profile_id, scenario.id, attribute.id)
        score = get_score(scores, profile_id, scenario.id, alternative.id)
        contribution = attribute_contribution(entry, score)
        context[f"score_{slug}"] = score
        context[f"attribute_weight_{slug}"] = entry.global_weight
        context[f"global_weight_{slug}"] = entry.global_weight
        context[f"local_weight_{slug}"] = entry.local_weight
        context[f"effective_weight_{slug}"] = effective_weight(entry)
        context[f"contribution_{slug}"] = contribution
        context[f"global_weight_{slug}"] = effective_weight(entry)

    for index, indexed_scenario in enumerate(scenarios, start=1):
        indexed_abs = calculate_abs(
            alternative=alternative,
            profile_id=profile_id,
            scenario_id=indexed_scenario.id,
            attributes=attributes,
            weight_entries=weight_entries,
            scores=scores,
        )
        indexed_score = get_score(scores, profile_id, indexed_scenario.id, alternative.id)
        indexed_normalized_weight = normalized_scenario_weights.get(indexed_scenario.id, 0.0)
        context[f"abs_{index}"] = indexed_abs
        context[f"score_{index}"] = indexed_score
        context[f"scenario_weight_{index}"] = indexed_scenario.weight
        context[f"normalized_scenario_weight_{index}"] = indexed_normalized_weight
        context[f"weighted_abs_{index}"] = calculate_weighted_abs(
            indexed_abs,
            indexed_normalized_weight,
        )
        scenario_global_total = 0.0
        scenario_attribute_total = 0.0
        scenario_local_total = 0.0
        for attribute in attributes:
            slug = slugify_identifier(attribute.name)
            indexed_entry = get_weight_entry(
                weight_entries,
                profile_id,
                indexed_scenario.id,
                attribute.id,
            )
            indexed_contribution = attribute_contribution(indexed_entry, indexed_score)
            indexed_effective_weight = effective_weight(indexed_entry)
            scenario_attribute_total += indexed_entry.global_weight
            scenario_local_total += indexed_entry.local_weight
            scenario_global_total += indexed_effective_weight
            context[f"attribute_weight_{slug}_{index}"] = indexed_entry.global_weight
            context[f"global_weight_{slug}_{index}"] = indexed_effective_weight
            context[f"local_weight_{slug}_{index}"] = indexed_entry.local_weight
            context[f"effective_weight_{slug}_{index}"] = indexed_effective_weight
            context[f"contribution_{slug}_{index}"] = indexed_contribution
        context[f"attribute_weight_{index}"] = round(scenario_attribute_total, 6)
        context[f"local_weight_{index}"] = round(scenario_local_total, 6)
        context[f"global_weight_{index}"] = round(scenario_global_total, 6)
    return context


def build_aggregate_formula_context(
    alternative: Alternative,
    profile_id: str,
    scenarios: list[Scenario],
    attributes: list[Attribute],
    weight_entries: list[WeightEntry],
    scores: list[ScoreEntry],
    alpha: float,
    beta: float,
    cost_score: float,
    risk_score: float,
) -> dict[str, float]:
    normalized_scenario_weights = normalize_scenario_weights(scenarios)
    total_abs = 0.0
    total_weighted_abs = 0.0
    total_scenario_weight = 0.0
    total_normalized_scenario_weight = 0.0

    attribute_weight_totals: dict[str, float] = {}
    global_weight_totals: dict[str, float] = {}
    local_weight_totals: dict[str, float] = {}
    contribution_totals: dict[str, float] = {}
    score_totals: dict[str, float] = {}

    context: dict[str, float] = {
        "num_scenarios": float(len(scenarios)),
        "benefit_a": 0.0,
        "alpha": alpha,
        "beta": beta,
        "cost_score": cost_score,
        "cost_score_a": cost_score,
        "risk_score": risk_score,
        "risk_score_a": risk_score,
    }

    for index, scenario in enumerate(scenarios, start=1):
        abs_value = calculate_abs(
            alternative=alternative,
            profile_id=profile_id,
            scenario_id=scenario.id,
            attributes=attributes,
            weight_entries=weight_entries,
            scores=scores,
        )
        scenario_score = get_score(scores, profile_id, scenario.id, alternative.id)
        normalized_weight = normalized_scenario_weights.get(scenario.id, 0.0)
        weighted_abs = calculate_weighted_abs(abs_value, normalized_weight)

        total_abs += abs_value
        total_weighted_abs += weighted_abs
        total_scenario_weight += scenario.weight
        total_normalized_scenario_weight += normalized_weight

        context[f"abs_{index}"] = abs_value
        context[f"score_{index}"] = scenario_score
        context[f"scenario_weight_{index}"] = scenario.weight
        context[f"normalized_scenario_weight_{index}"] = normalized_weight
        context[f"weighted_abs_{index}"] = weighted_abs

        scenario_attribute_total = 0.0
        scenario_local_total = 0.0
        scenario_global_total = 0.0
        for attribute in attributes:
            slug = slugify_identifier(attribute.name)
            entry = get_weight_entry(weight_entries, profile_id, scenario.id, attribute.id)
            effective = effective_weight(entry)
            contribution = attribute_contribution(entry, scenario_score)

            scenario_attribute_total += entry.global_weight
            scenario_local_total += entry.local_weight
            scenario_global_total += effective

            attribute_weight_totals[slug] = attribute_weight_totals.get(slug, 0.0) + entry.global_weight
            global_weight_totals[slug] = global_weight_totals.get(slug, 0.0) + effective
            local_weight_totals[slug] = local_weight_totals.get(slug, 0.0) + entry.local_weight
            contribution_totals[slug] = contribution_totals.get(slug, 0.0) + contribution
            score_totals[slug] = score_totals.get(slug, 0.0) + scenario_score

            context[f"attribute_weight_{slug}_{index}"] = entry.global_weight
            context[f"global_weight_{slug}_{index}"] = effective
            context[f"local_weight_{slug}_{index}"] = entry.local_weight
            context[f"effective_weight_{slug}_{index}"] = effective
            context[f"contribution_{slug}_{index}"] = contribution

        context[f"attribute_weight_{index}"] = round(scenario_attribute_total, 6)
        context[f"local_weight_{index}"] = round(scenario_local_total, 6)
        context[f"global_weight_{index}"] = round(scenario_global_total, 6)

    context["abs"] = round(total_abs, 6)
    context["benefit_a"] = round(total_abs, 6)
    context["weighted_abs"] = round(total_weighted_abs, 6)
    context["scenario_weight"] = round(total_scenario_weight, 6)
    context["normalized_scenario_weight"] = round(total_normalized_scenario_weight, 6)

    for attribute in attributes:
        slug = slugify_identifier(attribute.name)
        context[f"score_{slug}"] = round(score_totals.get(slug, 0.0), 6)
        context[f"attribute_weight_{slug}"] = round(attribute_weight_totals.get(slug, 0.0), 6)
        context[f"global_weight_{slug}"] = round(global_weight_totals.get(slug, 0.0), 6)
        context[f"local_weight_{slug}"] = round(local_weight_totals.get(slug, 0.0), 6)
        context[f"effective_weight_{slug}"] = round(global_weight_totals.get(slug, 0.0), 6)
        context[f"contribution_{slug}"] = round(contribution_totals.get(slug, 0.0), 6)

    return context


def _expand_summations(
    latex_expression: str,
    variables: Mapping[str, float],
) -> str:
    variable_names = set(variables.keys())
    indexed_pattern = re.compile(
        r"\\sum_\{([a-zA-Z])\s*=\s*([0-9]+)\}\^\{([^{}]+)\}\(([^()]+)\)"
    )
    wildcard_pattern = re.compile(r"\\sum_\{([^{}]+)\}|\\sum\{([^{}]+)\}|\\sum\(([^()]+)\)")

    def replace_indexed(match: re.Match[str]) -> str:
        index_name = match.group(1).strip()
        start = int(match.group(2).strip())
        upper_raw = match.group(3).strip()
        body = match.group(4).strip()
        if re.fullmatch(r"[0-9]+", upper_raw):
            upper = int(upper_raw)
        else:
            if upper_raw not in variables:
                raise ValueError(f"Unsupported summation upper bound: {upper_raw}")
            upper = int(float(variables[upper_raw]))
        if upper < start:
            return "(0)"
        expanded_terms: list[str] = []
        for current_index in range(start, upper + 1):
            replaced_body = re.sub(
                rf"\b([A-Za-z_][A-Za-z0-9_]*)_{index_name}\b",
                rf"\1_{current_index}",
                body,
            )
            expanded_terms.append(f"({replaced_body})")
        return "(" + " + ".join(expanded_terms) + ")"

    def replace(match: re.Match[str]) -> str:
        wildcard = next(group for group in match.groups() if group is not None).strip()
        regex = "^" + re.escape(wildcard).replace(r"\*", ".*") + "$"
        matched_names = sorted(
            variable_name
            for variable_name in variable_names
            if re.fullmatch(regex, variable_name)
        )
        if not matched_names:
            raise ValueError(f"No variables match summation pattern: {wildcard}")
        return "(" + " + ".join(matched_names) + ")"

    expression = indexed_pattern.sub(replace_indexed, latex_expression)
    return wildcard_pattern.sub(replace, expression)


def latex_to_expression(
    latex_expression: str,
    variables: Mapping[str, float] | None = None,
) -> str:
    expression = latex_expression.strip()
    if variables:
        expression = _expand_summations(expression, variables)
    expression = expression.replace("Benefit(A)", "benefit_a")
    expression = expression.replace("cost_score(A)", "cost_score_a")
    expression = expression.replace("risk_score(A)", "risk_score_a")
    expression = expression.replace("\\left", "").replace("\\right", "")
    expression = expression.replace("\\cdot", "*").replace("\\times", "*")
    expression = expression.replace("^", "**")
    expression = _replace_fractions(expression)
    expression = expression.replace("{", "(").replace("}", ")")
    expression = re.sub(r"\\,", "", expression)
    expression = re.sub(r"\s+", " ", expression).strip()
    return expression


def _replace_fractions(expression: str) -> str:
    while "\\frac" in expression:
        start = expression.find("\\frac")
        numerator_start = expression.find("{", start)
        numerator_end = _matching_brace_index(expression, numerator_start)
        denominator_start = expression.find("{", numerator_end + 1)
        denominator_end = _matching_brace_index(expression, denominator_start)
        numerator = expression[numerator_start + 1 : numerator_end]
        denominator = expression[denominator_start + 1 : denominator_end]
        replacement = f"(({_replace_fractions(numerator)})/({_replace_fractions(denominator)}))"
        expression = expression[:start] + replacement + expression[denominator_end + 1 :]
    return expression


def _matching_brace_index(expression: str, start_index: int) -> int:
    depth = 0
    for index in range(start_index, len(expression)):
        if expression[index] == "{":
            depth += 1
        elif expression[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unbalanced braces in LaTeX expression.")


def evaluate_formula(expression: str, variables: Mapping[str, float]) -> float:
    tree = ast.parse(expression, mode="eval")
    return float(_eval_ast(tree.body, variables))


def _eval_ast(node: ast.AST, variables: Mapping[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Unsupported variable: {node.id}")
        return float(variables[node.id])
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        return _ALLOWED_BIN_OPS[type(node.op)](
            _eval_ast(node.left, variables),
            _eval_ast(node.right, variables),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return _ALLOWED_UNARY_OPS[type(node.op)](_eval_ast(node.operand, variables))
    raise ValueError("Unsupported expression. Use arithmetic, parentheses, and known variables.")


def evaluate_formula_result(formula: Formula, context: Mapping[str, float]) -> float | None:
    try:
        expression = latex_to_expression(formula.latex, context)
        return round(evaluate_formula(expression, context), 4)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError):
        return None


def validate_formula(latex_expression: str, allowed_variables: set[str]) -> tuple[bool, str]:
    sample_context = {name: 1.0 for name in allowed_variables}
    sample_context.update({
        "abs": 1.0,
        "num_scenarios": 3.0,
        "scenario_weight": 0.5,
        "normalized_scenario_weight": 0.5,
        "weighted_abs": 0.5,
        "score_1": 1.0,
        "score_2": 1.0,
        "score_3": 1.0,
        "global_weight_1": 1.0,
        "global_weight_2": 1.0,
        "global_weight_3": 1.0,
        "weighted_abs_1": 1.0,
        "weighted_abs_2": 1.0,
        "weighted_abs_3": 1.0,
    })
    try:
        expression = latex_to_expression(latex_expression, sample_context)
        evaluate_formula(expression, sample_context)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
        return False, str(exc)
    return True, ""


def format_metric(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"
