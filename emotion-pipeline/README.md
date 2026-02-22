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

## Tavus persona (Full Pipeline + Raven + Custom LLM)

SPECTRA uses Full Pipeline mode with Raven-1 perception **and** a Custom LLM
that routes to our backend instead of Tavus's built-in LLM.  This keeps
perception + STT active while preventing Tavus from generating its own
responses (all speech is delivered via `conversation.echo`).

> **Why not Echo mode?** Tavus docs say echo mode is "incompatible with
> perception and speech recognition layers".  SPECTRA needs Raven-1 for
> emotion detection, so we use Custom LLM mode instead.

### 1. Start an ngrok tunnel to your backend

```bash
ngrok http 8000   # note the https://xxxx.ngrok.io URL
```

### 2. Create / update the persona

```bash
export TAVUS_API_KEY="tvus_..."
export BACKEND_PUBLIC_URL="https://xxxx.ngrok.io"

# Create new persona
./emotion-pipeline/update_persona.sh

# — or update existing —
./emotion-pipeline/update_persona.sh p53b88f7ef1e
```

The script replaces `$$BACKEND_PUBLIC_URL$$` in `tavus_persona.json` and
calls the Tavus API.

### 3. Create a conversation

```bash
curl -X POST https://tavusapi.com/v2/conversations \
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
