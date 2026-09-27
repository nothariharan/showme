# Bob evaluation plan

You are IBM Bob. The repo is `C:\Users\HARIHARAN\Desktop\Bob\showme`. Your only job is to evaluate ShowMe and write the evidence down. Do not add features. Do not change product code to make a test pass. Do not invent numbers that a command did not print.

Work from this directory for every command:

```
C:\Users\HARIHARAN\Desktop\Bob\showme
```

Python is already installed. Run commands with `python`, not a virtualenv, unless `python` is missing. If it is missing, write that in `eval/bugs.md` and stop.

## Why this run exists

ShowMe compiles two demonstrations into an Agent Skill, then proves the skill against a local billing portal. A good run writes a tax PDF. A bad customer writes nothing. A renamed button stops the run instead of clicking a neighbor. The repeat does not call a model.

The tests are the proof. Your report is what a person reads after you finish. Screenshots of your task summary are for the hackathon. The markdown files are the evaluation.

## What you write

Create `eval/logs/` and these files. Overwrite them on this run. Do not leave them empty.

| File | What goes in it |
| --- | --- |
| `eval/logs/unittest.txt` | Full stdout and stderr of the suite, plus the exit code on the last line |
| `eval/logs/prove-1042.txt` | The live prove command and `proof.json` |
| `eval/logs/prove-0000.txt` | The unknown-customer prove command and `proof.json` |
| `eval/logs/prove-renamed.txt` | The renamed-button prove command and `proof.json` |
| `eval/findings.md` | Every check that ran, why it exists, pass or fail, and the evidence path |
| `eval/bugs.md` | Only failures. If nothing failed, the file still exists and says no bugs |
| `eval/loops/pass-1.md` | What pass 1 ran and its exit codes |
| `eval/loops/pass-2.md` | The confirmation pass |

Quote command output. Do not paraphrase a failure into a guess about the cause unless you also paste the assertion line.

## How a row is written

`eval/findings.md` uses this table. One row per check. Add rows. Do not delete the header.

```markdown
# Findings

| Check | Why | Result | Evidence |
| --- | --- | --- | --- |
| suite | The repo's own tests are the contract | PASS or FAIL, exit N | eval/logs/unittest.txt |
```

`eval/bugs.md` uses this table. One row per failed check.

```markdown
# Bugs

| Id | Check | Command | Exit | Expected | Actual | Evidence | Rerun |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | prove 0000 | python -m showme prove ... | 0 | exit 1 and no PDF | exit 0 and a PDF | eval/logs/prove-0000.txt | confirmed or not rerun |
```

If a check passes, it does not appear in `eval/bugs.md`.

## The loop

Do not stop after the first command. Do not stop after the first failure. Finish pass 1, write the files, then do pass 2, then stop.

Pass 1 runs every check below, in order, even when an earlier check fails.

Pass 2 does not explore new ideas. It re-runs:

- the full suite once more, always
- every command that failed in pass 1, once more

Then update the Rerun column. If pass 2 disagrees with pass 1, say so in both files. Do not start pass 3.

## Pass 1

### 1. Record the environment

Run:

```
python --version
python -c "import sys; print(sys.executable)"
```

Put both lines at the top of `eval/loops/pass-1.md`.

### 2. The suite

Why: these 28 tests are the contract. They cover parsing, compile, file replay, the portal, induction, and prove.

```
python -W default -m unittest discover -s tests -v
```

Save the complete output to `eval/logs/unittest.txt`. Append a final line `exit N`.

Expected: exit 0, and the output contains `Ran 28 tests` and `OK`.

What each file is for, so you can name a failure:

| File | What a failure means |
| --- | --- |
| `tests/test_model.py` | A demonstration was accepted or rejected for the wrong reason |
| `tests/test_compile.py` | The Agent Skill folder is missing `SKILL.md`, `references/trace.json`, or `scripts/replay.py`, or a second compile overwrote a skill |
| `tests/test_sort_replay.py` | The local player moved the wrong files, or it overwrote a file it should have refused |
| `tests/test_cli.py` | `validate`, `compile`, or `run` disagreed with the library |
| `tests/test_portal_run.py` | The same skill did not export two customers, or a missing customer still wrote a PDF, or a click ran before the page was open |
| `tests/test_induce.py` | Two runs did not become parameters, a changed click was accepted, or a renamed button was clicked anyway |
| `tests/test_prove.py` | The proof file lied: a good customer failed, a bad customer wrote a PDF, or a renamed button did not stop the run |

A failed test is a bug row. Copy the test name and the assertion from the log. Do not fix it in this pass.

### 3. Live prove, customer 1042

Why: the suite can pass while the command you would hand a person is broken. This runs the command itself.

```
python -m showme validate examples/export-customer-pdf/demonstration.json
python -m showme compile examples/export-customer-pdf/demonstration.json --out eval/logs/skills-1042
```

Compile fails if `eval/logs/skills-1042/export-customer-pdf` already exists. Delete that directory first if it is there, then compile again.

Start the portal in the background. Do not wait for it to exit. It prints one port and then stays up:

```
python -c "import sys; sys.path.insert(0, 'examples/billing_portal'); import server; from pathlib import Path; d=Path('eval/logs/dl-1042'); d.mkdir(parents=True, exist_ok=True); h=server.start(d); print(h.server_address[1], flush=True); import time; time.sleep(3600)"
```

Read the port from that output. Then, with `PORT` replaced, run prove. After prove finishes, stop the portal process. Do not leave it running.

```
python -m showme prove eval/logs/skills-1042/export-customer-pdf --download-dir eval/logs/dl-1042 --set customer_id=1042 --set portal_url=http://127.0.0.1:PORT
```

Then stop the portal process.

Expected:

- Exit 0
- Stdout contains `proof ok`
- `eval/logs/dl-1042/proof.json` has `"ok": true`, a `url` ending in `/billing/customer/1042/export`, and an `artifact` path
- `eval/logs/dl-1042/tax-1042.pdf` exists and its text contains `1042`, `Acme`, and `120.00`

Save the command output and the full `proof.json` into `eval/logs/prove-1042.txt`.

### 4. Live prove, customer 0000

Why: a missing customer must not look like success.

Use a new download directory, `eval/logs/dl-0000`. Start the portal the same way, pointed at that directory. Compile into `eval/logs/skills-0000` if you need a fresh skill, or reuse the skill from step 3. Run prove with `customer_id=0000` and that portal URL.

Expected:

- Exit 1
- `eval/logs/dl-0000/proof.json` has `"ok": false`
- No file named `tax-0000.pdf` in that directory

Save output and `proof.json` to `eval/logs/prove-0000.txt`. Stop the portal.

### 5. Live prove, renamed button

Why: the product stops when the label is gone. It must not click another control and it must not write a PDF.

Start this portal in the background. Do not wait for it to exit. The export button is renamed:

```
python -c "import sys; sys.path.insert(0, 'examples/billing_portal'); import server; from pathlib import Path; d=Path('eval/logs/dl-renamed'); d.mkdir(parents=True, exist_ok=True); h=server.start(d, export_label='Download PDF'); print(h.server_address[1], flush=True); import time; time.sleep(3600)"
```

Prove customer 1042 against that port, download dir `eval/logs/dl-renamed`. Stop the portal when the command returns.

Expected:

- Exit 1
- `proof.json` has `"ok": false` and an `error` that contains `Export PDF` and `Download PDF`
- `tax-1042.pdf` does not exist in that directory

Save output and `proof.json` to `eval/logs/prove-renamed.txt`. Stop the portal.

### 6. The page, by reading files

Why: the marketing page must match the software. You do not need a browser for this check.

Read `site/index.html` and `site/styles.css`.

Expected, and write one findings row for each:

- The headline text `Show it once. Prove it on a clean machine. Any agent can run it.` is in `site/index.html`
- `styles.css` sets the background to `#0b0c10`
- `styles.css` names `Redaction` and `Schibsted Grotesk`
- The page names the prove command
- The page does not contain `100%`, `3.8 seconds`, `62%`, or `45,000`

A missing phrase is a bug row. Quote the search, not a summary.

## Pass 2

Re-run the suite:

```
python -W default -m unittest discover -s tests -v
```

Save it to `eval/logs/unittest-pass-2.txt` with `exit N` on the last line.

Re-run only the live prove commands that failed in pass 1. If none failed, do not start the portal again.

Write `eval/loops/pass-2.md` with the exit code and whether it matched pass 1.

Update `eval/findings.md` if a result flipped. Update the Rerun column in `eval/bugs.md`.

## When you stop

Stop after pass 2. Write this block at the bottom of `eval/findings.md`:

```markdown
## Stop

- Pass 1 suite exit:
- Pass 2 suite exit:
- Live prove 1042:
- Live prove 0000:
- Live prove renamed:
- Bug count:
- Ready for a person to read: yes or no
```

Ready is yes only when pass 2's suite exit is 0, the three live proves match the expected results above, and every bug from pass 1 was either confirmed or cleared on the rerun.

Leave the task summary on screen. That screenshot is the hackathon record of this run.
