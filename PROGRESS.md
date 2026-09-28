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

## Task 4: CP4 reliability (Redis store, readiness, graceful shutdown)
- Implemented `ping`, `append`, and `get_history` in `ConversationStore` (`app/store.py`) using Redis operations with message trimming and TTL.
- Implemented graceful shutdown handling in `Lifecycle` (`app/lifecycle.py`) to manage shutdown status and signal delegation for SIGTERM and SIGINT.
- Added readiness probe endpoint `/ready` in `app/main.py` responding based on lifecycle shutdown state and Redis connection status.
- Added `tests/test_cp4.py` to `testpaths` in `pytest.ini`.

## Task 5: Customer-support theme + /usage endpoint
- Configured SERVICE_NAME to "customer-support-agent" and updated FastAPI title to "Customer Support Agent" in app/main.py.
- Implemented authenticated GET /usage endpoint returning current quota, rate limits, spent USD, and remaining budget without recording rate-limit hits or calling the LLM.
- Created tests/test_support.py validating /usage authentication, metrics calculation, rate-limit bypassing, and /health reporting.
- Added tests/test_support.py to testpaths in pytest.ini.
- Documented customer support theme and /usage endpoint usage with curl in README.md.

## Task 6: Bonus CI/CD workflow + README badge
- Created GitHub Actions CI/CD workflow in `.github/workflows/ci.yml` with `test`, `build`, and `deploy` jobs triggered on push to main and pull requests.
- Configured pinned action versions (`actions/checkout@v4`, `actions/setup-python@v5`), automated dependency installation, and pytest execution in the CI test job.
- Added Docker image build step and automated Railway deployment gated behind successful test passes on the main branch.
- Added the GitHub Actions CI workflow status badge under the main title in `README.md`.
- Added `tests/test_bonus_cicd.py` to `testpaths` in `pytest.ini` and verified the full test suite passes.
