# oracle-brain

WebSocket service that turns game context (Contract 2) into oracle replies (Contract 3) using Claude. Part of the Spectra ORACLE 3-phase mission.

## Run

```bash
cd oracle-brain
pip install -r requirements.txt
```

Set `ANTHROPIC_API_KEY` in the repo root `.env`, then:

- **Live (Claude API):** `python claude_client.py` → `ws://localhost:8765`
- **Mock (no API):** `python claude_client.py --mock`

Send one JSON message (Contract 2) per request; receive Contract 3 (oracle text, UI commands, game update) or `{"error": "..."}` on invalid input.

## Modules

- **claude_client.py** — WebSocket server; calls Claude with `system_prompt.txt`, falls back to `../mock-data/oracle_response.json` on API failure.
- **scenarios.py** — Phase templates (infiltrate → vault → escape): openings, options, transitions, and `next_phase()`.

## Tests

```bash
python -m pytest test_claude_client.py test_scenarios.py -v
```
