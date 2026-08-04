# Test fixtures

## `sisjuri_2026_01..06.json`

Real SISJURI closing snapshots for the six **closed** months of 2026, one per file, as
stored by the agent. They are the regression guard for every DB-derived number the app
shows, so keep them **all on the same extract contract** — a fixture missing a key does
not fail, it makes the tests that read it pass VACUOUSLY (that is how the vale day-count
test once claimed "41 rows" while checking 6; and how the old Feb stub, at 11 of 29 keys,
pinned legacy code paths that production had long since replaced).

### Regenerating

```bash
cd backend
python -m scripts.dump_fixture --all-2026        # Jan..Jun (closed months only)
```

⚠ These are the guard for the client-facing numbers. After refreshing, run `pytest` and
**explain every expectation that moves before changing it** — a refresh that quietly
re-baselines an assertion turns a guard into a rubber stamp. The June per-área cells the
client validated (Contencioso 75.424,21 · Econômico 80.536,85 · Arbitragem 54.383,94) must
not move at all. There is deliberately no fixture for the OPEN month: it changes under you,
so a fixture of it would make the suite's result depend on the day it runs.

## `legaldesk_2026_05.json`

A recorded **real** LegalDesk payload for competence month **2026-05**, captured
via the verified `build_payload` pipeline. It is committed so the test suite can
run fully offline and so the verified headline totals stay **locked** as a
regression guard (`receita_honorarios=415927.84`, `faturamento_realizado=719988.05`,
`faturas_emitidas=53`).

### Regenerating

With real LegalDesk credentials available (set `LEGALDESK_PASSWORD` in the
environment), regenerate by running the builder for the period and writing the
returned payload to this file:

```python
import json
from app.closing.builder import build_payload
from app.closing.period import Period
from app.sources.legaldesk_client import LegalDeskClient

payload = build_payload(Period.parse("2026-05"), LegalDeskClient())
json.dump(payload, open("backend/tests/fixtures/legaldesk_2026_05.json", "w"))
```
