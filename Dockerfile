FROM ghcr.io/astral-sh/uv:0.8.15-python3.13-alpine AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --all-extras --no-dev --no-group test
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --all-extras --no-dev --no-group test

FROM python:3.13-alpine

RUN apk --update-cache upgrade \
    && apk add --no-interactive mimalloc \
    && apk cache purge \
    && rm -rf /var/cache/apk/*

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV LD_PRELOAD="/usr/lib/libmimalloc.so.2"

USER app

WORKDIR /app
VOLUME /app/data
ENTRYPOINT ["/app/.venv/bin/litestar", "run", "--host", "0.0.0.0"]
