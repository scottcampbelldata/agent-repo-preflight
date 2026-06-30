from __future__ import annotations
import os
import uvicorn
from .app import create_app


def main() -> None:
    host = os.environ.get("AGENT_PREFLIGHT_HOST", "127.0.0.1")
    port = int(os.environ.get("AGENT_PREFLIGHT_PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
