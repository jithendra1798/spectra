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

## Mapper test

```bash
python emotion-pipeline/test_mapper.py emotion-pipeline/fixtures/utterance.example.json
```

## Expected output

Logs of raw `conversation.utterance` payloads (and optionally all app-message
payloads with `--log-all`).
