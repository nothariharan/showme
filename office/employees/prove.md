# Prove

Branch: `prove`
Worktree: sibling `showme-prove`

Build `showme prove`.

- Input: a compiled skill directory, `--set name=value` pairs, and `--download-dir`.
- Run the skill with `HtmlSession` the same way `showme run` does for an all-agent skill.
- Success proof: the finished page body contains `Download started`, and `download-dir/tax-<customer>.pdf` exists and contains that customer id. Write `proof.json` into the download dir with `ok: true`, the final URL, and the artifact path.
- Unknown customer: the run raises, `ok` is false, and no PDF is written.
- Renamed button: do not click anything else. The error names the missing label and the visible controls.
- Tests live in `tests/test_prove.py` and use `examples/billing_portal/server.py` plus `examples/export-customer-pdf/demonstration.json`.
- Leave `site/` and `assets/` alone.

State: done
