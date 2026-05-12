# Machine Learning Testing Conventions

ML testing extends [python.md](python.md) (testing). Standard Python testing rules apply; this document adds the ML-specific concerns: data, features, model behavior, training reproducibility, and serving.

## Local Environment Isolation (MANDATORY)

All ML tests run inside the project's virtual environment. The test command must be invoked **after** activating `.venv/`. Test runners that try to "auto-install missing packages" globally are forbidden.

```bash
source .venv/bin/activate
which python  # must point inside .venv/
pytest
```

## Test Categories

ML systems require five distinct test layers. None of them is optional.

| Layer | Purpose | Lives in |
|-------|---------|----------|
| Data tests | Schema, distribution, leakage, PII | `tests/data/` |
| Feature tests | Determinism, point-in-time correctness | `tests/features/` |
| Model tests | Behavior on known inputs, regression, slices, fairness | `tests/models/` |
| Pipeline tests | Training reproducibility, end-to-end run | `tests/pipeline/` |
| Serving tests | Inference API contract, latency, error modes | `tests/serving/` |

## Test Structure

```
tests/
├── conftest.py
├── data/
│   ├── test_schema.py            # Column types, ranges, nullability
│   ├── test_distribution.py      # Class balance, drift sentinels
│   └── test_pii.py               # No PII in non-PII columns
├── features/
│   ├── test_transforms.py        # Deterministic given the same input
│   └── test_point_in_time.py     # No future leakage
├── models/
│   ├── test_behavior.py          # Output shape, monotonicity, sanity checks
│   ├── test_slices.py            # Performance on protected/important slices
│   └── test_fairness.py          # Demographic parity / equal opportunity
├── pipeline/
│   ├── test_reproducibility.py   # Same seed + same data → same metrics
│   └── test_end_to_end.py        # Tiny synthetic dataset round-trip
├── serving/
│   ├── test_api_contract.py      # Pydantic schemas, status codes, error modes
│   └── test_latency.py           # p99 < target on warm cache
└── fixtures/
    ├── tiny_dataset.parquet      # Small enough to run in CI
    └── golden_predictions.json   # Reference outputs for regression tests
```

## Data Tests

```python
def test_schema_columns_present(training_df):
    """Required columns must exist in every training batch."""
    expected = {"user_id", "feature_a", "feature_b", "label"}
    assert expected.issubset(training_df.columns)

def test_no_pii_in_features(training_df):
    """Feature columns must not contain raw PII per data architecture."""
    pii_pattern = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    for col in FEATURE_COLUMNS:
        assert not training_df[col].astype(str).str.contains(pii_pattern).any()

def test_class_balance_within_expected_range(training_df):
    """Positive class rate must stay within the documented range."""
    positive_rate = training_df["label"].mean()
    assert 0.05 <= positive_rate <= 0.25  # documented in 70-ml-{name}.md
```

## Feature Tests

```python
def test_transform_is_deterministic():
    """Same input → same output, across invocations."""
    raw = sample_input()
    a = transform(raw)
    b = transform(raw)
    assert_frame_equal(a, b)

def test_no_future_leakage():
    """Features at time T must not depend on rows with timestamp > T."""
    df = build_training_set(as_of="2024-01-01")
    for col in TIME_SENSITIVE_FEATURES:
        assert df[col + "_source_timestamp"].max() <= pd.Timestamp("2024-01-01")
```

## Model Tests

Model tests answer: *does the model behave the way the design says it should?* They are not "is the model accurate enough" — that lives in the offline evaluation pipeline.

```python
def test_output_shape(loaded_model, sample_batch):
    """Output shape matches the contract in 70-ml-{name}.md."""
    output = loaded_model.predict(sample_batch)
    assert output.shape == (len(sample_batch), N_CLASSES)

def test_known_strong_signal_pushes_prediction(loaded_model):
    """Documented strong signals should move the prediction in the expected direction."""
    baseline = loaded_model.predict(neutral_example())
    boosted = loaded_model.predict(strong_positive_example())
    assert boosted[0, POSITIVE_CLASS] > baseline[0, POSITIVE_CLASS]

def test_metric_floor_on_holdout(loaded_model, holdout_set):
    """Refuse to ship a model below the design's acceptance threshold."""
    auc = roc_auc(loaded_model, holdout_set)
    assert auc >= ACCEPTANCE_THRESHOLD  # from 70-ml-{name}.md §7.1

def test_no_regression_on_protected_slice(loaded_model, slice_dataset):
    """Performance on the protected slice must not regress beyond the documented bound."""
    for slice_name, slice_df in slice_dataset.items():
        auc = roc_auc(loaded_model, slice_df)
        assert auc >= SLICE_FLOORS[slice_name]
```

## Pipeline Tests

```python
def test_training_is_reproducible(tmp_path):
    """Same config + same data + same seed → bit-identical metrics."""
    metrics_a = train(config="configs/test.yaml", artifact_dir=tmp_path / "a")
    metrics_b = train(config="configs/test.yaml", artifact_dir=tmp_path / "b")
    assert metrics_a == metrics_b

def test_end_to_end_tiny_dataset(tmp_path):
    """A 100-row synthetic dataset must run through ingest → train → evaluate → register."""
    run_pipeline(config="configs/tiny.yaml", artifact_dir=tmp_path)
    assert (tmp_path / "model.safetensors").exists()
    assert (tmp_path / "metrics.json").exists()
```

## Serving Tests

```python
async def test_predict_endpoint_contract(async_client):
    """Inference endpoint matches the 50-api-contracts.md schema."""
    response = await async_client.post("/predict", json={"feature_a": 1.0, "feature_b": "x"})
    assert response.status_code == 200
    body = response.json()
    assert {"prediction", "score", "model_version"}.issubset(body.keys())

async def test_predict_rejects_malformed_input(async_client):
    """Missing required field returns 422."""
    response = await async_client.post("/predict", json={})
    assert response.status_code == 422

async def test_predict_fallback_when_model_unavailable(async_client, monkeypatch):
    """When the predictor raises, the documented fallback kicks in."""
    monkeypatch.setattr("pkg.serving.predictor.Predictor.predict", lambda self, r: raise_(RuntimeError))
    response = await async_client.post("/predict", json=valid_payload())
    assert response.status_code == 200
    assert response.json()["source"] == "fallback"
```

## Golden Tests (Regression)

For models with known-stable behavior, keep a small set of (input, prediction) pairs in `tests/fixtures/golden_predictions.json`. Tests assert the loaded model's predictions match within a documented tolerance. When the model intentionally changes behavior, the golden file is updated as part of the same PR — never silently.

## Forbidden Patterns

- Asserting on `==` for floating-point predictions. Use `pytest.approx` with a documented tolerance.
- Test data sourced from the production database. Test fixtures are committed, synthetic, or sampled-then-anonymized.
- Tests that hit external APIs (model registry, vector DB, LLM provider) without a recorded fixture or local stub.
- Slow training tests in the default `pytest` run. Mark them `@pytest.mark.slow` and exclude from the fast CI lane.
- Mocking the model under test. Mock its inputs and outputs, never the model behavior itself — that defeats the purpose.

## Coverage Target

- Minimum 70% line coverage on `src/{pkg}/serving/`, `src/{pkg}/features/`, `src/{pkg}/data/`.
- Training code (`src/{pkg}/training/`) is covered by pipeline tests, not unit coverage — the meaningful test is the end-to-end run.
- Notebooks are excluded from coverage and from CI altogether.
