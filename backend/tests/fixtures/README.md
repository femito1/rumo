# Test fixtures

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
