# Backend Tests

This directory contains pytest tests for the ClipPilot Lite backend.

## Setup

Install test dependencies:
```bash
pip install pytest pytest-asyncio
```

## Running Tests

From the `backend` directory:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_health.py

# Run specific test function
pytest tests/test_health.py::test_health_check_returns_200

# Run with coverage
pytest --cov=app tests/
```

## Test Files

- **test_health.py** - Health check endpoint tests
- **test_config.py** - Configuration and Settings tests
- **test_jobs.py** - Job creation, status, result, and cancellation tests
- **conftest.py** - Pytest configuration and shared fixtures

## Fixtures

The following fixtures are available in `conftest.py`:

- `test_client` - FastAPI TestClient for the app
- `mock_supabase` - Mocked Supabase client
- `mock_redis` - Mocked Redis client
- `test_settings` - Test configuration with defaults
- `mock_get_supabase` - Patched get_supabase dependency
- `mock_get_redis` - Patched get_redis dependency
- `mock_auth` - Mocked authentication returning test user_id
- `authenticated_client` - Pre-authenticated test client

## Notes

- Tests use `unittest.mock` to mock external dependencies (Supabase, Redis)
- Tests do not require real API keys or external services
- Authentication is mocked to return a test user_id
- Most job endpoints require authentication and will return 401/403 without valid token
