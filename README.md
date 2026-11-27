# api
API for storing and accessing data from other sources

## Setup

### Get Postgres ready
- `psql -U postgres`
- `CREATE DATABASE "api.jonathanstegall";`
- `\list` to verify
- `q` to exit that thing and then `\q` to exit psql
- `alembic upgrade head` to setup the database

### Check if JSON is installed in Redis
- `redis-cli`
- `JSON.SET bike $ '"Hyperion"'`

### Run the app
- `uv sync` then `source .venv/bin/activate` (`uv add requests` to install libraries)
- `uv run fastapi dev` to start the app
- `http://127.0.0.1:8000` is the url where the app runs
- Running an ingest method will populate the links as desired. There's no reason to save the database from any previous installs unless it has more than one or two requests worth of data.
