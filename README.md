# Trade-Off Workbench

Trade-Off Workbench is a Reflex web application for building reusable multi-criteria trade studies across alternatives, quality attributes, weighted scenarios, and decision profiles.

## Current capabilities

- Persistent JSON storage on the deployed machine.
- Automatic reload of the last saved study when the app starts.
- Alternatives modeled with name and description only.
- Profile-based analysis focus with configurable name and description.
- Multiple reusable profiles with independent weights and scores.
- Scenario-specific configuration of:
  - scenario weight
  - global attribute weight
  - local attribute weight
  - 1-to-5 qualitative scores
- Aggregated results computed for the selected profile across all scenarios.
- Built-in `Architectural Benefit Score (ABS)` and `Scenario Weighted ABS`.
- Custom formulas written in a restricted LaTeX-like syntax.
- Variable picker for attribute scores, attribute weights, and built-in scenario variables.
- Transparent results tables, including a full configured-variable breakdown by option.

## Project structure

- `tradeoff_app/tradeoff_app.py`: Reflex state and UI composition.
- `tradeoff_app/domain/models.py`: core domain entities.
- `tradeoff_app/services/calculations.py`: metric logic and LaTeX-like formula evaluation.
- `tradeoff_app/services/storage.py`: JSON persistence layer.
- `tradeoff_app/data/sample_data.py`: editable sample dataset.
- `tradeoff_app/components/common.py`: shared visual building blocks.
- `docs/usage.md`: user guide.
- `docs/architecture.md`: architecture notes.

## Running locally

If the local virtual environment is already available:

```bash
REFLEX_DIR=.reflex-home .venv/bin/reflex run
```

If you need to rebuild the environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install reflex==0.8.28.post1
REFLEX_DIR=.reflex-home reflex run
```

To compile the frontend:

```bash
REFLEX_DIR=.reflex-home .venv/bin/reflex compile
```

## Persistence

- The application stores its shared state in `storage/tradeoff_state.json`.
- The dataset is saved automatically after every meaningful change.
- You can also force a save or reload the saved snapshot from the Overview tab.
