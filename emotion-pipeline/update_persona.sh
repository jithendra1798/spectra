#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SPECTRA — Create / Update Tavus persona with Custom LLM proxy
#
# Usage:
#   export TAVUS_API_KEY="tvus_..."
#   export BACKEND_PUBLIC_URL="https://xxxx.ngrok.io"   # your tunnel URL
#   ./emotion-pipeline/update_persona.sh
#
# This script:
#   1. Reads tavus_persona.json
#   2. Replaces $$BACKEND_PUBLIC_URL$$ with the env var
#   3. Creates a new persona via Tavus API (POST /v2/personas)
#
# To UPDATE an existing persona, pass its ID:
#   ./emotion-pipeline/update_persona.sh p53b88f7ef1e
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PERSONA_TEMPLATE="$SCRIPT_DIR/tavus_persona.json"

# ── Validate env ─────────────────────────────────────────────────────────────
: "${TAVUS_API_KEY:?Set TAVUS_API_KEY before running this script}"
: "${BACKEND_PUBLIC_URL:?Set BACKEND_PUBLIC_URL (e.g. https://xxxx.ngrok.io)}"

# ── Build request body ───────────────────────────────────────────────────────
# For PATCH: Tavus requires JSON Patch (RFC 6902) format
# For POST:  Tavus accepts a plain persona JSON body
PERSONA_JSON=$(sed "s|\\\$\\\$BACKEND_PUBLIC_URL\\\$\\\$|${BACKEND_PUBLIC_URL}|g" "$PERSONA_TEMPLATE")

echo "──────────────────────────────────────────────"
echo "Tavus Persona payload:"
echo "$PERSONA_JSON" | python3 -m json.tool 2>/dev/null || echo "$PERSONA_JSON"
echo "──────────────────────────────────────────────"

PERSONA_ID="${1:-}"

if [ -n "$PERSONA_ID" ]; then
    # ── PATCH existing persona (JSON Patch / RFC 6902) ───────────────────
    echo "Updating existing persona: $PERSONA_ID"

    # Build a JSON Patch array from the persona template fields
    PATCH_BODY=$(python3 -c "
import json, sys
persona = json.loads(sys.stdin.read())
ops = []
for key in ['persona_name','system_prompt','pipeline_mode']:
    if key in persona:
        ops.append({'op':'replace','path':'/'+key,'value':persona[key]})
layers = persona.get('layers', {})
for layer_name, layer_cfg in layers.items():
    ops.append({'op':'add','path':'/layers/'+layer_name,'value':layer_cfg})
json.dump(ops, sys.stdout)
" <<< "$PERSONA_JSON")

    echo "Patch ops:"
    echo "$PATCH_BODY" | python3 -m json.tool 2>/dev/null || echo "$PATCH_BODY"

    curl -s --max-time 120 -X PATCH "https://tavusapi.com/v2/personas/${PERSONA_ID}" \
        -H "Content-Type: application/json" \
        -H "x-api-key: ${TAVUS_API_KEY}" \
        -d "$PATCH_BODY" | python3 -m json.tool
else
    # ── POST new persona ─────────────────────────────────────────────────
    echo "Creating new persona..."
    RESPONSE=$(curl -s --max-time 120 -X POST "https://tavusapi.com/v2/personas" \
        -H "Content-Type: application/json" \
        -H "x-api-key: ${TAVUS_API_KEY}" \
        -d "$PERSONA_JSON")

    echo "$RESPONSE" | python3 -m json.tool

    NEW_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('persona_id','???'))" 2>/dev/null || echo "???")
    echo ""
    echo "✅  Persona created:  $NEW_ID"
    echo ""
    echo "Next steps:"
    echo "  1. Update backend/.env:  TAVUS_PERSONA_ID=$NEW_ID"
    echo "  2. Create a conversation:"
    echo "     curl -X POST https://tavusapi.com/v2/conversations \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -H 'x-api-key: \$TAVUS_API_KEY' \\"
    echo "       -d '{\"persona_id\": \"$NEW_ID\"}'"
fi
