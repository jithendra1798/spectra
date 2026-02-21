#!/usr/bin/env python3
"""
Oracle Brain — uvicorn runner.
"""

import os
import uvicorn

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("ORACLE_PORT", "8001"))

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )
