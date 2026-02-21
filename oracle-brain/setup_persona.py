"""
SPECTRA — One-time Tavus persona setup script.

Patches the Tavus persona to use oracle-brain as a Custom LLM so the
Tavus avatar speaks Claude's responses instead of the default Llama model.

Usage:
    # 1. Expose oracle-brain via ngrok (in a separate terminal):
    #    ngrok http 8001
    #
    # 2. Run this script with the public ngrok URL:
    #    ORACLE_PUBLIC_URL=https://abc123.ngrok-free.app python setup_persona.py
    #
    # The persona update persists in Tavus — you only need to run this once
    # per ngrok session (i.e., whenever the public URL changes).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

TAVUS_API = "https://tavusapi.com/v2"

api_key = os.environ.get("TAVUS_API_KEY", "")
persona_id = os.environ.get("TAVUS_PERSONA_ID", "")
oracle_public_url = os.environ.get("ORACLE_PUBLIC_URL", "").rstrip("/")

if not api_key:
    print("ERROR: TAVUS_API_KEY not set in environment or root .env")
    sys.exit(1)

if not persona_id:
    print("ERROR: TAVUS_PERSONA_ID not set in environment or root .env")
    sys.exit(1)

if not oracle_public_url:
    print("ERROR: ORACLE_PUBLIC_URL not set")
    print("  Run: ORACLE_PUBLIC_URL=https://xxx.ngrok-free.app python setup_persona.py")
    sys.exit(1)

llm_base_url = oracle_public_url + "/v1"

print(f"Patching Tavus persona {persona_id!r}")
print(f"  LLM base_url → {llm_base_url}")
print()

payload = {
    "layers": {
        "llm": {
            "model": "spectra-oracle",
            "base_url": llm_base_url,
            "api_key": "spectra-oracle-key",
        }
    }
}

resp = httpx.patch(
    f"{TAVUS_API}/personas/{persona_id}",
    json=payload,
    headers={"x-api-key": api_key},
    timeout=15.0,
)

print(f"Status: {resp.status_code}")
if resp.text:
    print(f"Body:   {resp.text[:400]}")

if resp.status_code in (200, 204):
    print()
    print("✓ Persona updated — oracle-brain is now the Tavus Custom LLM.")
    print("  Restart oracle-brain (python run.py) and create a new session to test.")
else:
    print()
    print("✗ Persona update failed — check TAVUS_PERSONA_ID and TAVUS_API_KEY.")
    sys.exit(1)
