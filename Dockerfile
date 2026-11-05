FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.18 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home omniref
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER omniref
EXPOSE 8000
# Container default is HTTP on all interfaces (no auth: run behind a proxy).
# Override with `docker run -i ... omniref --transport stdio` for stdio clients.
ENTRYPOINT ["omniref"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
