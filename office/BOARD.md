# Office board

This folder is how the workstreams stay in sync. Each employee writes only their own file. The office manager merges branches onto `main` after the tester is green.

## Rules

- `prove` may edit `src/showme/`, `tests/test_prove.py`, and `office/employees/prove.md`.
- `site` may edit `site/`, `assets/`, and `office/employees/site.md`.
- `tester` runs the suite and writes `office/employees/tester.md`. It does not change product code unless a test is wrong about the agreed behavior.
- Do not invent reliability percentages, token prices, GitHub stars, cryptographic seals, or a selector fallback that clicks a nearby control.
- A renamed control stops the run and names the labels on the page.

## Status

| Workstream | Branch | State |
| --- | --- | --- |
| prove | prove | done |
| site | site | done |
| tester | main | done |

## Done means

1. `python -m showme prove` writes a proof when the billing portal exports a real tax PDF, writes no PDF for an unknown customer, and halts when the export button is renamed.
2. `site/` renders the wsp-style page with honest copy and the generated assets.
3. `python -W default -m unittest discover -s tests -v` is OK.
4. Both branches are merged into local `main`.
