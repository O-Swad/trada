# Architecture Notes

## Goal

Keep the implementation simple, readable, and practical while separating domain rules from the Reflex UI.

## Layers

### Domain

`tradeoff_app/domain/models.py`

Contains the core entities used by the application:

- `Alternative`
- `Attribute`
- `Scenario`
- `Profile`
- `WeightEntry`
- `ScoreEntry`
- `Formula`

These classes isolate the problem space from the raw dictionary structures stored in Reflex state.

### Services

`tradeoff_app/services/calculations.py`

Encapsulates:

- ABS calculation
- profile-specific aggregation across all scenarios
- scenario-weight normalization
- effective-weight and contribution logic
- restricted LaTeX-like formula parsing
- safe arithmetic evaluation

`tradeoff_app/services/storage.py`

Encapsulates:

- JSON save/load operations
- filesystem location of the shared persisted snapshot

### State and Presentation

`tradeoff_app/tradeoff_app.py`

Contains:

- Reflex state
- mutation events
- profile-aware editing flows
- derived tables and chart datasets
- UI composition for Overview, Modeling, Formula Lab, and Results

### Shared Components

`tradeoff_app/components/common.py`

Provides reusable UI primitives for:

- section panels
- KPI cards
- reusable selects
- empty states

## Key decisions

- State remains JSON-serializable to make persistence straightforward.
- The application auto-saves after each meaningful mutation so the deployed instance behaves like a shared working tool.
- Custom formulas are parsed through a restricted `ast` evaluator instead of Python `eval`.
- Scenario weights are distinct from attribute global/local weights.
- Profiles are the primary analysis focus, and each profile owns its own weights and scores across all scenarios.
- All user-facing copy is kept in English.
