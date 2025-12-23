# Nuze Backend Load Testing

This directory contains load testing scripts using [Locust](https://locust.io/).

## Prerequisites

Ensure you have the development dependencies installed.
Since this project uses `uv`, you can easily run the tests using `uv run`.

## Running Load Tests

### 1. Web UI Mode (Recommended)
This starts the Locust web interface, where you can configure the test parameters interactively.

```bash
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```
Then open [http://localhost:8089](http://localhost:8089) in your browser.

### 2. Headless Mode (Command Line)
To run a quick test without the UI (useful for CI or quick checks):

```bash
# Run with 10 users, spawn rate of 2 users/sec, for 30 seconds
uv run locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000
```

## Test Scenarios
The `locustfile.py` defines a `NuzeUser` that:
1.  **On Start**: Registers a new random user and logs them in to obtain a JWT token.
2.  **Tasks**:
    - `health_check` (Weight 1): Calls `/health`.
    - `get_feed` (Weight 5): Calls `/feed/` with the JWT token.
    - `stress_auth` (Weight 3): repeatedly calls `/auth/login`.
