## Requirements

* Python 3.11

## Installation

Install modules with poetry configured in pyproject.toml and poetry.lock:

```
pip install poetry
poetry install --with dev
```

In order for pre-commit hooks to work, install them:
```
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```


## Create .env from .env.example
```
slack_channel=""
slack_api_token=""
slack_timeout=10

service_name = " "
CIRCUIT_SNAME = "local"
sentry_dsn = " "
redis_cluster = " "
swagger_public_api_url = " "
swagger_internal_api_url = " "
version = " "
```
