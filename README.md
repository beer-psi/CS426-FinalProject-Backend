# CS426 Final Project backend

This is the backend for the CS426 - Mobile Device Application Development.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Simply [install uv](https://docs.astral.sh/uv/getting-started/installation/)
and set up a development environment by running:

```
uv sync
```

Activate the created virtual environment:

```shell
source .venv/bin/activate
# .venv/Scripts/Activate.ps1 on Windows
```

Create the database by creating the `data/` folder and run:

```
litestar database setup
```

## Migrations

Create a database migration by running:

```
litestar migrate add "migration description"
```

Apply any pending migrations by running:

```
litestar migrate run
```

Revert migrations by running:

```
litestar migrate revert
```

## Just

This repository contains a `Justfile` for common operations. Start by reading its [installation instructions](https://github.com/casey/just?tab=readme-ov-file#installation).
