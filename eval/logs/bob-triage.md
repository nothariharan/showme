# Bob triage — openclaw/openclaw

Written by IBM Bob (Agent mode) from `C:\Users\HARIHARAN\Desktop\Bob\showme`.

---

## How the run was called

The MCP tool `showme_triage` wraps `showme run .agents/skills/triage-repo --browser`.
For this session the CLI command was called directly (equivalent to what the MCP tool executes):

```
python -m showme run .agents/skills/triage-repo --browser \
    --set owner=openclaw \
    --set repo=openclaw
```

Working directory: `C:\Users\HARIHARAN\Desktop\Bob\showme`

Exit code: **0**

Runner output:
```
wrote 14 issues to notes/issues.md
wrote 20 pulls to notes/pulls.md
finished on https://github.com/openclaw/openclaw/pulls
```

No titles were invented. Every title was extracted from the live GitHub pages by
`notes.py:matching_links()`, which only accepts links whose href matches
`/issues/\d+$` or `/pull/\d+$`.

---

## Skill used

`.agents/skills/triage-repo/SKILL.md` — compiled from
`examples/triage-repo/demonstration.json`.

Parameters: `owner` and `repo` (induced from two recordings:
`openai/openai-agents-python` and `google/adk-js`).

Trace: `navigate → note_links(issues) → click(Pull requests) → navigate → note_links(pulls)`

---

## notes/issues.md (14 issues)

```
# issues

- Contributor / Maintainer Start Here
  https://github.com/openclaw/openclaw/issues/84599
- PR Limit Update: Why We Now Cap at 20 Open PRs Per Author
  https://github.com/openclaw/openclaw/issues/38283
- Gateway boots ~7 short-lived SQLite store/read workers per minute (512 MB each), keeping V8 threads at ~80% CPU
  https://github.com/openclaw/openclaw/issues/159638
- [Bug]: view_image forwards undecodable images verbatim; one truncated JPEG permanently breaks a session
  https://github.com/openclaw/openclaw/issues/159637
- Subagent completion settlement retries forever: "owner changed before settlement" re-injects result every turn
  https://github.com/openclaw/openclaw/issues/159612
- [Feature]: Support page text extraction for existing-session browsers
  https://github.com/openclaw/openclaw/issues/159610
- 2026.9.6 on macOS with 20 agents: off-heap RSS growth to 6 GB, per-agent Codex app-servers on restart recovery, upgrade blocked by deferred plugin session index, no downgrade path
  https://github.com/openclaw/openclaw/issues/159606
- [Bug]: Gateway memory sawtooth on 2026.9.6 — prepared-model-catalog worker grows to the full heap ceiling; ~200 critical memory-pressure events/day
  https://github.com/openclaw/openclaw/issues/159596
- Update failure: unexpected-error (2026.9.4)
  https://github.com/openclaw/openclaw/issues/159591
- Update failure: global-install-failed (2026.9.4)
  https://github.com/openclaw/openclaw/issues/159579
- [Feature]: Add a host-owned quiet-period progress supervisor
  https://github.com/openclaw/openclaw/issues/159575
- [Feature]: Opt-in Skill Workshop experience review for persistent agentTurn automations
  https://github.com/openclaw/openclaw/issues/159570
- [Bug/Regression] Gateway event loop freezes and WebUI becomes intermittently unavailable on 1 GB OCI VM after upgrading to 2026.9.6
  https://github.com/openclaw/openclaw/issues/159551
- [Bug]: pdf tool resolves no model for an agent on OpenRouter although the agent's own model reads PDFs once named — the tool is exposed and fails "No PDF model configured."
  https://github.com/openclaw/openclaw/issues/159542
```

---

## notes/pulls.md (20 pull requests)

```
# pulls

- test(packages): remove low-value tests (batch d067)
  https://github.com/openclaw/openclaw/pull/159645
- fix(update): prevent migrated results from appearing before cleanup
  https://github.com/openclaw/openclaw/pull/159644
- fix(test): stabilize SQLite integrity diagnostic fixtures
  https://github.com/openclaw/openclaw/pull/159643
- fix(test): preserve human provenance in release recovery fixture
  https://github.com/openclaw/openclaw/pull/159642
- refactor(skills): reuse fs-safe for artifact snapshots
  https://github.com/openclaw/openclaw/pull/159641
- docs(cloud-workers): profile setup still tells operators to restart the Gateway
  https://github.com/openclaw/openclaw/pull/159640
- refactor(agents): deslop agent tools third pass
  https://github.com/openclaw/openclaw/pull/159639
- fix: keep reply admission responsive during database contention
  https://github.com/openclaw/openclaw/pull/159632
- fix: child tasks fail to resume during background recovery
  https://github.com/openclaw/openclaw/pull/159628
- fix(cli): secrets store list help calls env values non-secret metadata
  https://github.com/openclaw/openclaw/pull/159626
- fix(test): prepare matching Control UI assets before E2E
  https://github.com/openclaw/openclaw/pull/159624
- feat(browser): extract page text from existing Chrome sessions
  https://github.com/openclaw/openclaw/pull/159623
- fix(ios): typing-focus test flakes inside UIKit's nested keyboard run loop
  https://github.com/openclaw/openclaw/pull/159622
- fix(computer): reject malformed actions before desktop setup
  https://github.com/openclaw/openclaw/pull/159621
- refactor(agents): share image provider test fixtures
  https://github.com/openclaw/openclaw/pull/159620
- fix(sqlite): reduce session write stalls during cleanup
  https://github.com/openclaw/openclaw/pull/159619
- refactor(agents): reuse subagent announce test fixtures
  https://github.com/openclaw/openclaw/pull/159618
- fix(code-mode): avoid worker startup heap exhaustion
  https://github.com/openclaw/openclaw/pull/159615
- fix(infra): name the lock path in gateway lock timeout errors
  https://github.com/openclaw/openclaw/pull/159614
- feat(activity): today pulse, whole-row highlight, and quieter row actions
  https://github.com/openclaw/openclaw/pull/159611
```

---

## Checks

| Check | Result |
| --- | --- |
| Tool/command finished without error | PASS — exit 0 |
| issues.md exists with openclaw/openclaw issue links | PASS — 14 issues, all `github.com/openclaw/openclaw/issues/N` |
| pulls.md exists with openclaw/openclaw pull links | PASS — 20 PRs, all `github.com/openclaw/openclaw/pull/N` |
| No invented titles — all from live GitHub | PASS — extracted by regex from page DOM, not generated |
| trace.json still has `owner` and `repo` parameters | PASS — not edited |

Notes files: `.agents/skills/triage-repo/notes/issues.md` and `.agents/skills/triage-repo/notes/pulls.md`
