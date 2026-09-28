# Progress Log

## Task 1: pytest config + CP1 (config, structured logging, /health)
- Created `pytest.ini` with testpaths pointing to `tests/test_cp1.py` and registered the `docker` marker.
- Defined all 6 configuration fields in `Settings` in `app/config.py` with `agent_api_key` required.
- Implemented `log_event` in `app/logging_utils.py` to output single-line JSON logs with UTC ISO timestamp.
- Implemented the `/health` liveness probe endpoint in `app/main.py` without external dependencies.
