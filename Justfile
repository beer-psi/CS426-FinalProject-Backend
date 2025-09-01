default:
    @just --choose

dev:
    litestar run --debug --reload --reload-dir app
