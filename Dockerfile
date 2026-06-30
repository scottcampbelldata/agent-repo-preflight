# syntax=docker/dockerfile:1
# Web demo image for agent-repo-preflight.
# Build:  docker build -t agent-repo-preflight .
# Run:    docker run -p 8000:8000 -v preflight-data:/data agent-repo-preflight

FROM python:3.12-slim AS build
WORKDIR /app
# Build a wheel from the source tree so the runtime image stays clean.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim
# Run as a non-root user.
RUN useradd --create-home --uid 10001 app
WORKDIR /app

# Install just the built wheel with the [web] extra.
COPY --from=build /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir "$(ls /tmp/*.whl)[web]" && rm -f /tmp/*.whl

# Bundle the example repos so the /examples page works on a fresh deploy.
COPY examples ./examples

# Persist the SQLite scan store on a volume.
ENV AGENT_PREFLIGHT_DB=/data/preflight.db \
    AGENT_PREFLIGHT_HOST=0.0.0.0 \
    AGENT_PREFLIGHT_PORT=8000 \
    AGENT_PREFLIGHT_EXAMPLES_DIR=/app/examples
RUN mkdir -p /data && chown app:app /data
VOLUME ["/data"]

USER app
EXPOSE 8000

# Lightweight healthcheck against the home page.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/').status==200 else 1)"

CMD ["python", "-m", "agent_repo_preflight.web"]
