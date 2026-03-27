# Usage Guide

## 1. Overview

The **Overview** tab lets you:

- rename the study
- describe the decision context
- save the current dataset to JSON
- reload the saved dataset
- restore the built-in sample
- choose the active profile used by the analysis
- choose the active scenario used by the detailed modeling views

### Profiles

Profiles represent the decision posture you want to test, such as `Risk Aversion` or `Future Proof`.

Each profile has:

- name
- description

Every profile keeps its own:

- scenario-by-attribute weights
- scenario-by-alternative scores

## 2. Modeling

The **Modeling** tab contains five areas:

### Alternatives

Add the trade options you want to compare. Each alternative only needs:

- name
- description

### Quality Attributes

Add the qualitative dimensions used in the study. Each attribute has:

- name
- description

### Scenarios

Add scenarios with:

- name
- description
- scenario weight from `0` to `1`

### Scenario Weight Matrix

For the selected profile and selected scenario, define:

- global weight for each attribute
- local weight for each attribute

Both weights are constrained to the `0` to `1` interval.

### Score Matrix

For the selected profile and selected scenario, enter a score from `1` to `5` for each:

- alternative
- attribute

The app computes:

`ABS = sum(global_weight * local_weight * score)`

## 3. Formula Lab

The **Formula Lab** lets you define custom metrics using a restricted LaTeX-like syntax.

Supported building blocks include:

- variables
- numbers
- `+`
- `-`
- `\cdot`
- `\times`
- `\frac{a}{b}`
- parentheses
- powers with `^`

Built-in variables include:

- `abs`
- `scenario_weight`
- `normalized_scenario_weight`
- `weighted_abs`

For every attribute, the app also exposes:

- `score_<attribute>`
- `global_weight_<attribute>`
- `local_weight_<attribute>`
- `effective_weight_<attribute>`
- `contribution_<attribute>`

Example:

```latex
\frac{contribution_evolvability + contribution_operability}{scenario_weight}
```

## 4. Results

The **Results** tab includes:

- a per-scenario summary table for the active profile
- an aggregated ranking across all scenarios for the active profile
- ABS and weighted ranking charts
- weighted score comparison by scenario
- score radar chart
- global-weight sensitivity chart
- a full configured-variable table for the active profile across all scenarios

The configured-variable table is designed to make interpretation explicit by showing, for each profile, scenario, option, and attribute:

- profile
- scenario
- scenario weight
- global weight
- local weight
- effective weight
- score
- contribution
