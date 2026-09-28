# Progress Log

## Task 1: pytest config + CP1 (config, structured logging, /health)
- Created `pytest.ini` with testpaths pointing to `tests/test_cp1.py` and registered the `docker` marker.
- Defined all 6 configuration fields in `Settings` in `app/config.py` with `agent_api_key` required.
- Implemented `log_event` in `app/logging_utils.py` to output single-line JSON logs with UTC ISO timestamp.
- Implemented the `/health` liveness probe endpoint in `app/main.py` without external dependencies.

## Task 2: CP2 Docker (Dockerfile, .dockerignore, compose)
- Implemented a multi-stage Dockerfile with python:3.11-slim, builder virtualenv, non-root user (appuser), urllib-based healthcheck, and shell-form CMD for dynamic PORT support.
- Updated .dockerignore to exclude local secrets, virtualenvs, cache files, test artifacts, and markdown docs while retaining required source files.
- Added the agent service to docker-compose.yml with port mapping, environment variable interpolation, Redis dependency with healthy condition, and service healthcheck.
- Updated pytest.ini testpaths to include both tests/test_cp1.py and tests/test_cp2.py.

## Task 3: CP3 API security (auth, rate limit, cost guard, /ask)
- Implemented API key authentication in `app/auth.py` using `secrets.compare_digest` to prevent timing attacks.
- Implemented sliding-window rate limiting in `app/rate_limiter.py` using Redis sorted sets (ZSET) with 429 Retry-After responses.
- Implemented monthly budget tracking and enforcement in `app/cost_guard.py` with 402 Payment Required responses.
- Connected authentication, rate limiter, cost guard, mock LLM, conversation store, and logging in `/ask` endpoint in `app/main.py`.
- Added `tests/test_cp3.py` to `testpaths` in `pytest.ini`.
