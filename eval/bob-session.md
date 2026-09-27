# Bob session — prove suite

Written by IBM Bob (Agent mode) from the ShowMe repo at
`C:\Users\HARIHARAN\Desktop\Bob\showme`.

---

## 1. Test suite

Command:

```
python -W default -m unittest discover -s tests -v
```

Result:

```
Ran 37 tests in 12.061s
OK
```

Exit code: 0. All 37 tests passed. No failures, no skips, no errors.

Tests covered: model validation, compile layout, sort replay, portal run, CLI,
induction, prove, record (capture + bundle + browser flag + MCP tool).

---

## 2. Compile

```
python -m showme validate examples/export-customer-pdf/demonstration.json
```

Output: `export-customer-pdf: 6 steps, 2 parameters` — exit 0.

```
python -m showme compile examples/export-customer-pdf/demonstration.json \
    --out eval/logs/skills-bob-session
```

Output: `eval\logs\skills-bob-session\export-customer-pdf` — exit 0.

Skill directory written:

```
eval/logs/skills-bob-session/export-customer-pdf/
├── SKILL.md
├── references/trace.json
└── scripts/replay.py
```

---

## 3. Live prove — customer 1042

The billing portal was started in the background on a random port (62633).
After prove returned, the portal process was stopped.

Command:

```
python -m showme prove eval/logs/skills-bob-session/export-customer-pdf \
    --download-dir eval/logs/dl-bob-session \
    --set customer_id=1042 \
    --set portal_url=http://127.0.0.1:62633
```

Stdout: `proof ok eval\logs\dl-bob-session\tax-1042.pdf`

Exit code: 0.

`eval/logs/dl-bob-session/proof.json`:

```json
{
  "ok": true,
  "url": "http://127.0.0.1:62633/billing/customer/1042/export",
  "artifact": "eval\\logs\\dl-bob-session\\tax-1042.pdf"
}
```

`eval/logs/dl-bob-session/tax-1042.pdf` (raw text):

```
tax summary for 1042 Acme amount 120.00
```

PDF contains `1042` ✓, `Acme` ✓, `120.00` ✓.

---

## Summary

| Check | Result |
| --- | --- |
| Suite (37 tests) | PASS — exit 0 |
| validate | PASS — exit 0 |
| compile | PASS — exit 0 |
| prove customer 1042 | PASS — exit 0, ok: true, PDF present |
| proof.json ok: true | ✓ |
| URL ends /billing/customer/1042/export | ✓ |
| PDF contains 1042, Acme, 120.00 | ✓ |
