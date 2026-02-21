# Emotion Pipeline — Checkpoint 1 (Python)

This module joins a Daily room as a participant and listens for Tavus
`conversation.utterance` events via app-message.

## Files

- `emotion-pipeline/daily_listener.py` — join + log utterance events
- `emotion-pipeline/mapper.py` — utterance → Contract 1 + player speech
- `emotion-pipeline/test_mapper.py` — local mapper test harness
- `emotion-pipeline/fixtures/utterance.example.json` — example utterance payload
- `emotion-pipeline/requirements.txt` — Python dependency (`daily-python`)

## Usage

```bash
pip install -r emotion-pipeline/requirements.txt

# Required
export TAVUS_CONVERSATION_URL="https://<your-daily-room>.daily.co/<room>"

# Optional (if your Daily room requires a token)
export DAILY_TOKEN="<token>"

export BACKEND_WS_URL="ws://localhost:8000"
export SESSION_ID="<session_id>"

python emotion-pipeline/daily_listener.py --log-all --backend-ws "$BACKEND_WS_URL" --session-id "$SESSION_ID"
```

## Tavus persona (Full Pipeline + Raven)

To enable perception in `conversation.utterance` events, use Full Pipeline with Raven.
This repo includes a starter persona config:

`emotion-pipeline/tavus_persona.json`

Create a persona with:

```bash
curl -X POST https://api.tavus.io/v2/personas \
  -H "Content-Type: application/json" \
  -H "x-api-key: $TAVUS_API_KEY" \
  --data @emotion-pipeline/tavus_persona.json
```

Then create a conversation using the returned `persona_id` and your `replica_id`:

```bash
curl -X POST https://api.tavus.io/v2/conversations \
  -H "Content-Type: application/json" \
  -H "x-api-key: $TAVUS_API_KEY" \
  -d '{
    "persona_id": "<persona_id>",
    "replica_id": "<replica_id>"
  }'
```

Use the `conversation_url` from the response in:
- `VITE_TAVUS_CONVERSATION_URL` (frontend iframe)
- `TAVUS_CONVERSATION_URL` (emotion pipeline)

## Mapper test

```bash
python emotion-pipeline/test_mapper.py emotion-pipeline/fixtures/utterance.example.json
```

## Expected output

Logs of raw `conversation.utterance` payloads (and optionally all app-message
payloads with `--log-all`).
