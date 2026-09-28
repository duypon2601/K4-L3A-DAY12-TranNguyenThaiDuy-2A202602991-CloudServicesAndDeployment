# Day 12 Cloud Deployment Lab — Customer Support Agent

TEST_CMD: .venv/bin/python -m pytest -q -m "not docker" -k "not test_badge_bao_passing"

## Overview
Theme: the agent is a public **customer support assistant**. Many customers
share one public URL, so API-key auth, per-customer rate limiting and a
per-customer monthly cost guard are what keep the bill under control.
`X-User-Id` is the customer id.

Stack: Python 3.11, FastAPI, pydantic-settings, Redis (fakeredis in tests),
pytest. Venv at `.venv/` (already installed; do not install packages).

Layout: `app/` is where code goes (`config.py`, `logging_utils.py`, `main.py`,
`auth.py`, `rate_limiter.py`, `cost_guard.py`, `store.py`, `lifecycle.py`).
Every stub raises `NotImplementedError` and its docstring gives the exact
TODO steps — follow them literally and keep the existing docstrings/comments
(Vietnamese) in place, replacing only the `raise NotImplementedError(...)`
lines / TODO bodies. `utils/mock_llm.py` is given: never modify it.
Never modify anything under `tests/` except creating new test files when a
task says so, and never modify `grade.py`.

Tests: `pytest.ini` `testpaths` controls which test files TEST_CMD runs; each
task adds its checkpoint file there. `tests/test_cp5.py` (needs a live
deployment) stays out of `testpaths`. Docker-build tests are excluded with
`-m "not docker"`.

Agent rules: you may only run the commands allowed in `.autowf.env`
(`git` read-only subcommands, `.venv/bin/python`, `ls`, `mkdir`), one per
call, never chained with `;`, `&&`, `|`, `$(...)` or backticks. Do not use
MCP tools; use CLI commands only. Do not commit — autowf commits.

## Task 1: pytest config + CP1 (config, structured logging, /health)
- Create `pytest.ini` with:
  ```ini
  [pytest]
  testpaths = tests/test_cp1.py
  markers =
      docker: needs a running Docker daemon
  ```
- `app/config.py`: declare the 6 `Settings` fields from the docstring table
  (`agent_api_key: str` with NO default).
- `app/logging_utils.py`: implement `log_event` per its docstring (one-line
  JSON to stdout, lowercase level, ISO timestamp, extra fields merged, return
  the string).
- `app/main.py`: implement `/health` — 503 `{"status": "shutting_down"}` when
  `lifecycle.shutting_down`, else `{"status": "ok", "service": SERVICE_NAME,
  "version": SERVICE_VERSION}`. No parameters, no Redis.

**Acceptance criteria:** TEST_CMD exits 0 and runs all of `tests/test_cp1.py`
(0 failures, 0 errors).

## Task 2: CP2 Docker (Dockerfile, .dockerignore, compose)
- `Dockerfile`: multi-stage — `FROM python:3.11-slim AS builder` installs
  `requirements.txt` into a venv (e.g. `/opt/venv`) with
  `COPY requirements.txt .` before `RUN pip install --no-cache-dir ...`;
  runtime stage `FROM python:3.11-slim` copies the venv, then `COPY app/ app/`
  and `COPY utils/ utils/` (after pip install); create a non-root user and
  switch with `USER`; `ENV PORT=8000`; `EXPOSE 8000`; `HEALTHCHECK` calling
  `/health` with python urllib (slim has no curl) on `${PORT}`;
  `CMD` in shell form `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`
  so the cloud-assigned `PORT` is honoured. No secrets, no word `password`.
  Keep the header comment block.
- `.dockerignore`: add `.env`, `.venv`, `__pycache__`, `*.pyc`,
  `.pytest_cache`, `tests`, `screenshots`, `.github`, `.auto-logs`, `*.md`;
  never ignore `app`, `utils`, `requirements.txt`.
- `docker-compose.yml`: add service `agent` — `build: .`, `ports: ["8000:8000"]`,
  environment `AGENT_API_KEY: ${AGENT_API_KEY}`, `REDIS_URL: redis://redis:6379/0`,
  `RATE_LIMIT_PER_MINUTE`, `MONTHLY_BUDGET_USD`, `LOG_LEVEL` via `${VAR:-default}`;
  `depends_on: redis` (condition `service_healthy`); a `healthcheck` calling
  `/health` with python urllib. Keep the existing `redis` service.
- `pytest.ini`: `testpaths = tests/test_cp1.py tests/test_cp2.py`.

**Acceptance criteria:** TEST_CMD exits 0 and includes `tests/test_cp2.py`
(`TestDockerfile`, `TestDockerignore`, `TestDockerCompose` all pass; the
`docker`-marked build tests are deselected).

## Task 3: CP3 API security (auth, rate limit, cost guard, /ask)
- `app/auth.py`: `verify_api_key` per docstring, comparing with
  `secrets.compare_digest`; 401 `"invalid or missing API key"`; return
  `x_user_id` or `ANONYMOUS_USER`.
- `app/rate_limiter.py`: `hit_count` and `check` per docstrings (sliding
  window ZSET, check before record, unique member, 429 with `Retry-After`).
- `app/cost_guard.py`: `spent`, `check` (402 `"monthly budget exceeded"`),
  `record` (`incrbyfloat` + `expire`) per docstrings.
- `app/main.py`: implement `/ask` in the exact 8-step order of its docstring.
- `pytest.ini`: add `tests/test_cp3.py` to `testpaths`.

**Acceptance criteria:** TEST_CMD exits 0 and includes `tests/test_cp3.py`
(auth, rate limiter, cost guard and `/ask` tests all pass).

## Task 4: CP4 reliability (Redis store, readiness, graceful shutdown)
- `app/store.py`: `ping` (try/except → bool), `append` (rpush JSON, ltrim to
  `HISTORY_MAX_MESSAGES`, expire), `get_history` (lrange + json.loads).
- `app/lifecycle.py`: `request_shutdown` (set flag, call previous handler if
  callable) and `install` (remember old handler, then register for SIGTERM
  and SIGINT).
- `app/main.py`: implement `/ready` per docstring (503 when shutting down or
  `store.ping()` is False, else `{"status": "ready", "redis": True}`).
  No module-level dict/list holding state.
- `pytest.ini`: add `tests/test_cp4.py` to `testpaths`.

**Acceptance criteria:** TEST_CMD exits 0 and includes `tests/test_cp4.py`
(store, stateless, readiness and graceful-shutdown tests all pass).

## Task 5: Customer-support theme + /usage endpoint
- `app/main.py`: `SERVICE_NAME = "customer-support-agent"`, FastAPI
  `title="Customer Support Agent"`. Add `GET /usage` (auth via
  `verify_api_key`, uses `get_rate_limiter` and `get_cost_guard`
  dependencies; does NOT call the LLM and does NOT record a rate-limit hit)
  returning `{"user_id", "requests_last_minute", "rate_limit_per_minute",
  "spent_usd", "monthly_budget_usd", "budget_remaining_usd"}` where
  remaining = `max(0.0, budget - spent)`. Use `limiter.hit_count`,
  `limiter.limit`, `guard.spent`, `guard.budget`.
- Create `tests/test_support.py` using the conftest fixtures
  (`client`, `client_factory`, `auth_headers`, `fake_redis`) with tests:
  `/usage` without key → 401; fresh customer → `requests_last_minute == 0`,
  `spent_usd == 0`, `budget_remaining_usd == monthly_budget_usd`; after two
  `/ask` calls → `requests_last_minute == 2` and `spent_usd > 0`; calling
  `/usage` repeatedly with `client_factory(rate_limit=1)` never returns 429;
  `/health` reports `service == "customer-support-agent"`.
- `pytest.ini`: add `tests/test_support.py` to `testpaths`.
- `README.md`: add a short section (Vietnamese, after "Mục Tiêu") titled
  `## Chủ Đề: Trợ Lý Hỗ Trợ Khách Hàng` explaining the theme and the `/usage`
  endpoint with one curl example (placeholder key `$AGENT_API_KEY`).

**Acceptance criteria:** TEST_CMD exits 0 and includes `tests/test_support.py`
with all the tests above passing; CP1–CP4 tests still pass.

## Task 6: Bonus CI/CD workflow + README badge
- Create `.github/workflows/ci.yml`:
  - `on:` `push` (branches `main`) and `pull_request`.
  - job `test`: `actions/checkout@v4`, `actions/setup-python@v5`
    (python 3.11), `pip install -r requirements.txt`, then
    `pytest -q -m "not docker" tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py tests/test_support.py`.
  - job `build`: `needs: test`, `docker build -t customer-support-agent:ci .`.
  - job `deploy`: `needs: [test, build]`,
    `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`,
    installs the Railway CLI (`npm install -g @railway/cli`) and runs
    `railway up --service ${{ secrets.RAILWAY_SERVICE }} --detach` with env
    `RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}`.
  - Every `uses:` pinned to a version tag (no `@main/@master/@latest`); no
    hardcoded tokens.
- `README.md`: add under the title
  `![CI](https://github.com/duypon2601/K4-L3A-DAY12-TranNguyenThaiDuy-2A202602991-CloudServicesAndDeployment/actions/workflows/ci.yml/badge.svg)`.
- `pytest.ini`: add `tests/test_bonus_cicd.py` to `testpaths` (the badge
  "passing" test needs a pushed repo and is deselected by TEST_CMD's `-k`).

**Acceptance criteria:** TEST_CMD exits 0 and includes
`tests/test_bonus_cicd.py` (all tests except `test_badge_bao_passing` pass).
