# Machine Learning Conventions

These conventions apply to all ML code: training pipelines, feature engineering, inference services, and offline analysis scripts. They sit on top of [python.md](python.md) — base Python rules apply unless overridden here.

Naming, case, and cross-layer serialization rules are owned by **ADR-001** (`project-docs/adrs/ADR-001-naming-conventions.md`). These conventions defer to ADR-001 for any cross-layer identifier question.

## Local Environment Isolation (MANDATORY)

ML projects pull in heavy dependencies (torch, cuda, scientific stack) and routinely break each other if installed globally. **All ML work runs inside a project-local virtual environment.** No exceptions.

| Step | Command |
|------|---------|
| Create venv | `python -m venv .venv` |
| Activate (bash) | `source .venv/bin/activate` |
| Verify | `which python` must point inside `.venv/` before any install |
| Install deps | `pip install -r requirements.txt` **(only after activation)** |

- **NEVER** run `pip install` outside an active project venv.
- **NEVER** run `sudo pip install` or `pip install --user`.
- **NEVER** install ML system libraries (CUDA, MKL, OpenMP) into the host OS during the workflow. If they are required, document them in [60-infrastructure.md](../../design-docs/60-infrastructure.md) as a base-image requirement; do not install them at training time.
- `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`, and `mlruns/` must be in `.gitignore`.

## Project Structure

```
project/
├── src/
│   └── {package_name}/
│       ├── data/                # Data loading & preprocessing
│       │   ├── ingest.py
│       │   └── splits.py
│       ├── features/            # Feature engineering
│       │   ├── transforms.py
│       │   └── feature_store.py
│       ├── models/              # Model definitions
│       │   ├── architecture.py
│       │   └── loss.py
│       ├── training/            # Training loop
│       │   ├── train.py         # Entry point
│       │   ├── config.py
│       │   └── reproducibility.py
│       ├── evaluation/          # Offline evaluation
│       │   ├── metrics.py
│       │   └── slices.py
│       ├── serving/             # Inference service
│       │   ├── api.py
│       │   └── predictor.py
│       └── monitoring/          # Drift & performance checks
│           └── drift.py
├── notebooks/                   # Exploration only — NEVER imported by production code
├── configs/                     # Training/serving config files (YAML)
├── data/                        # Local data cache; ignored by git
├── artifacts/                   # Local model artifacts; ignored by git
├── tests/
├── pyproject.toml
└── requirements.txt
```

## Notebook Policy

- Notebooks live in `notebooks/` and are for **exploration and reporting only**.
- Production code (anything imported by `train.py`, `predictor.py`, or any CI-run module) **must not** import from a notebook.
- Notebooks must not be the source of training runs that produce promoted models. A promoted training run must come from `src/` code under version control.
- Strip notebook output before committing (`nbstripout` or equivalent) — committing cell outputs creates noisy diffs and can leak PII or secrets.

## Reproducibility (MANDATORY)

Every training run must be reproducible. A training script that is not reproducible is broken.

| Aspect | Requirement |
|--------|-------------|
| Random seed | Set seeds for `random`, `numpy`, `torch`/`tensorflow`, and any data shuffler. Log the seed. |
| Code version | Stamp the git SHA into the model artifact's metadata. Refuse to train on a dirty working tree unless `--allow-dirty` is passed. |
| Data version | Reference training data by an immutable identifier (snapshot ID, dataset hash, or DVC tag). Log it with the run. |
| Dependency version | Lock all dependencies (`requirements.txt` with pinned versions or `uv.lock` / `poetry.lock`). |
| Hyperparameters | Hyperparameters live in a config file (`configs/*.yaml`); never inline literals in `train.py`. Log the resolved config. |
| Run metadata | Every run logs: timestamp, seed, git SHA, data version, config hash, environment (Python + lib versions), compute (host, GPU type). |

## Approved Libraries

Defaults — the architect may override in an ADR.

| Purpose | Library | Notes |
|---------|---------|-------|
| Tensor framework | PyTorch | TensorFlow only when an existing ecosystem forces it |
| Classical ML | scikit-learn | For linear/tree baselines |
| Gradient boosting | XGBoost or LightGBM | Pick one project-wide |
| Tabular data | polars (preferred) or pandas | polars for large datasets |
| Dataframes on disk | parquet | Never raw CSV for production datasets |
| Experiment tracking | MLflow | Or W&B if the team has it already |
| Feature store | Feast | Only if features must be shared across models |
| Hyperparameter search | Optuna | Bayesian-based search |
| Model serving (Python) | FastAPI + a thin predictor module | Reuse the project's web framework choice |
| Validation (data) | Great Expectations or pandera | Schema + distribution checks |
| Reproducibility | hydra-core or pydantic-settings | Config management with override semantics |

**LLM-specific:**

| Purpose | Library | Notes |
|---------|---------|-------|
| LLM SDK | The provider's official SDK (anthropic, openai, etc.) | Never hand-roll the HTTP layer |
| Prompts | Pydantic models for input/output schemas | Validate before sending and after receiving |
| Tracing | OpenTelemetry or the provider's tracing hooks | Log token usage and latency per call |
| Eval | A purpose-built eval harness (lm-eval-harness, promptfoo, or in-house) | Never "test by eyeballing" |

## Training Script Structure

A training entry point follows this shape:

```python
# src/{pkg}/training/train.py
from {pkg}.training.config import TrainingConfig
from {pkg}.training.reproducibility import freeze_environment, stamp_artifact

def main(config: TrainingConfig) -> None:
    freeze_environment(config.seed)
    data = load_dataset(config.data)
    model = build_model(config.model)
    metrics = train_loop(model, data, config.training)
    artifact = package_artifact(model, metrics, config)
    stamp_artifact(artifact, git_sha=..., data_version=..., config_hash=...)
    register(artifact, config.registry)
```

- One entry point per training pipeline. No "run all the things" omnibus scripts.
- Side effects (writing artifacts, registering models, calling external APIs) are isolated to the bottom of `main()`, never inside `build_model`/`train_loop`.

## Inference Service Structure

```python
# src/{pkg}/serving/predictor.py
class Predictor:
    """Single-model inference wrapper. Loaded once at process start."""
    def __init__(self, artifact_uri: str): ...
    def predict(self, request: PredictRequest) -> PredictResponse: ...

# src/{pkg}/serving/api.py
@app.post("/predict")
async def predict(request: PredictRequest, predictor: Predictor = Depends(...)) -> PredictResponse:
    return predictor.predict(request)
```

- Request and response schemas are Pydantic models. They are the API contract — change them via the same versioning rules as any other API (see [50-api-contracts.md](../../design-docs/50-api-contracts.md)).
- The predictor never reads from disk or calls external services during a request. All artifacts are loaded at startup.
- Inference is non-blocking — use async for I/O, run CPU/GPU work in a thread/process pool.

## Data Handling

- PII handling follows the **Data Architecture** (`02-data-architecture.md`). ML code never adds new PII flows that aren't reflected there.
- Training data with PII must be masked, hashed, or excluded before any non-local processing.
- Never commit training data, model weights, or evaluation outputs to git. Use `artifacts/` and `data/` (both gitignored) for local work and a model/data registry for shared artifacts.
- All dataset operations preserve **point-in-time correctness** — features at training time must reflect what would have been available at the prediction's decision time.

## Configuration

- Training and serving configs live under `configs/` as YAML, loaded via a typed config object (pydantic or hydra).
- Secrets (API keys, model registry credentials) come from environment variables; never embedded in configs or code.
- Environment variables follow ADR-001 (`SCREAMING_SNAKE_CASE`).

## Build Commands

| Action | Command |
|--------|---------|
| Activate venv | `source .venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Train | `python -m {pkg}.training.train --config configs/train.yaml` |
| Evaluate offline | `python -m {pkg}.evaluation.run --artifact <uri>` |
| Serve | `uvicorn {pkg}.serving.api:app --host 0.0.0.0 --port 8000` |
| Lint | `ruff check .` |
| Type check | `mypy src/` |

## Code Style

- All training, evaluation, and inference code must be type-hinted.
- Functions that mutate disk, registry, or external state must declare it in the docstring.
- Use `pathlib.Path` for paths; never raw strings.
- Keep cells, fixtures, and reference values out of production code paths — they belong in `tests/` or `notebooks/`.

## Forbidden Patterns

- Calling `pickle.load` on untrusted artifacts. Use `safetensors`, `joblib` with checksum verification, or a model-registry-provided loader.
- `eval()` on user input or model output.
- Catching `Exception` to "hide" inference errors — surface them; the serving layer decides what to fall back to.
- Hardcoding model paths or registry URIs; always read from config.
- Logging raw user inputs or model outputs that contain PII. Apply the project's redaction policy first.
