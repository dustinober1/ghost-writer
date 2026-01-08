# Test Suite

This directory contains comprehensive tests for the Ghostwriter Forensic Analytics API backend.

## Test Coverage

The test suite aims for **100% code coverage** across all modules:

- **API Routes**: All endpoints in `app/api/routes/`
  - Authentication routes (`test_auth_routes.py`)
  - Analysis routes (`test_analysis_routes.py`)
  - Fingerprint routes (`test_fingerprint_routes.py`)
  - Rewrite routes (`test_rewrite_routes.py`)

- **Services**: Business logic in `app/services/`
  - Analysis service (`test_analysis_service.py`)
  - Fingerprint service (`test_fingerprint_service.py`)

- **Utilities**: Helper functions in `app/utils/`
  - Authentication utilities (`test_auth_utils.py`)
  - Text processing (`test_text_processing.py`)
  - Database check (`test_db_check.py`)

- **ML Models**: Machine learning components in `app/ml/`
  - Contrastive model (`test_contrastive_model.py`, `test_contrastive_model_edge_cases.py`)
  - Feature extraction (`test_feature_extraction.py`, `test_feature_extraction_edge_cases.py`)
  - Fingerprint generation (`test_fingerprint.py`, `test_fingerprint_edge_cases.py`)
  - DSPy rewriter (`test_dspy_rewriter.py`)

- **Models & Database**: Data models in `app/models/`
  - Database models (`test_models.py`)

- **Main Application**: FastAPI app in `app/main.py`
  - Main app tests (`test_main.py`)

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run with Coverage Report

```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-report=html
```

This will:
- Run all tests
- Generate a terminal coverage report
- Generate an HTML coverage report in `htmlcov/` directory

### Run Specific Test File

```bash
pytest tests/test_auth_routes.py
```

### Run Specific Test

```bash
pytest tests/test_auth_routes.py::test_register_success
```

### Run with Verbose Output

```bash
pytest -v
```

## Test Configuration

Tests are configured in:
- `pytest.ini`: Pytest configuration with coverage settings
- `.coveragerc`: Coverage.py configuration
- `conftest.py`: Shared fixtures and test setup

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- `db`: Fresh database session for each test (using SQLite in-memory)
- `client`: FastAPI test client with database override
- `test_user`: Pre-created test user
- `auth_headers`: Authentication headers for authenticated requests
- `reset_services`: Automatically resets global service instances between tests

## Test Database

Tests use an in-memory SQLite database (`sqlite:///./test.db`) to avoid requiring a full PostgreSQL setup. Each test gets a fresh database that is cleaned up after the test completes.

## Coverage Requirements

The test suite is configured to **fail if coverage drops below 100%**. This ensures that all code is tested and new code additions include corresponding tests.

To view coverage:
1. Run tests with coverage: `pytest --cov=app --cov-report=html`
2. Open `htmlcov/index.html` in a browser to see detailed coverage report

## Writing New Tests

When adding new code:

1. **Write tests first** (TDD approach) or alongside the code
2. **Test all code paths**: happy paths, error cases, edge cases
3. **Use fixtures** from `conftest.py` for common setup
4. **Mock external dependencies** (APIs, file system, etc.)
5. **Run tests locally** before committing
6. **Ensure 100% coverage** for new code

### Example Test Structure

```python
def test_feature_name_success(client, auth_headers):
    """Test successful feature operation."""
    response = client.post(
        "/api/endpoint",
        headers=auth_headers,
        json={"key": "value"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data


def test_feature_name_error(client, auth_headers):
    """Test error handling."""
    response = client.post(
        "/api/endpoint",
        headers=auth_headers,
        json={"invalid": "data"}
    )
    assert response.status_code == 400
```

## Troubleshooting

### Tests Failing with Import Errors

Make sure you're in the `backend` directory and have installed dependencies:

```bash
cd backend
pip install -r requirements-dev.txt
```

### Database Errors

Tests use SQLite, so no PostgreSQL setup is needed. If you see database errors, check that `conftest.py` is properly configured.

### Coverage Below 100%

If coverage is below 100%, check the HTML coverage report to see which lines are missing:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

Then add tests to cover the missing lines.

### Authentication Test Failures

Make sure `test_user` fixture is being used and passwords match between user creation and login tests.