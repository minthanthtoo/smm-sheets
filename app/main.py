#!/usr/bin/env python3
"""SMM App entrypoint."""
from __future__ import annotations

import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

