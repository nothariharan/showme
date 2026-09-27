# Findings

| Check | Why | Result | Evidence |
| --- | --- | --- | --- |
| suite pass 1 | These 28 tests are the contract — parsing, compile, file replay, the portal, induction, and prove | PASS, exit 0 | eval/logs/unittest.txt |
| prove-1042 | The suite can pass while the command a person runs is broken; this runs it live | PASS, exit 0 | eval/logs/prove-1042.txt |
| prove-1042 proof.json ok:true | `"ok": true` must be set by a successful prove | PASS | eval/logs/prove-1042.txt |
| prove-1042 url ends /billing/customer/1042/export | The URL recorded in proof.json must match the route proved | PASS | eval/logs/prove-1042.txt |
| prove-1042 tax-1042.pdf contains 1042 | The downloaded file must be for the right customer | PASS | eval/logs/prove-1042.txt |
| prove-1042 tax-1042.pdf contains Acme | The downloaded file must name the expected company | PASS | eval/logs/prove-1042.txt |
| prove-1042 tax-1042.pdf contains 120.00 | The downloaded file must show the expected amount | PASS | eval/logs/prove-1042.txt |
| prove-0000 exit 1 | A missing customer must not look like success | PASS, exit 1 | eval/logs/prove-0000.txt |
| prove-0000 proof.json ok:false | Failure must be recorded in the proof file | PASS | eval/logs/prove-0000.txt |
| prove-0000 no tax-0000.pdf | An unknown customer must never write a PDF | PASS | eval/logs/prove-0000.txt |
| prove-renamed exit 1 | The product stops when the label is gone; it must not click a neighbor | PASS, exit 1 | eval/logs/prove-renamed.txt |
| prove-renamed proof.json ok:false | The renamed-button stop must be recorded | PASS | eval/logs/prove-renamed.txt |
| prove-renamed error names Export PDF | The error message must identify the missing label | PASS | eval/logs/prove-renamed.txt |
| prove-renamed error names Download PDF | The error message must identify what is actually on the page | PASS | eval/logs/prove-renamed.txt |
| prove-renamed no tax-1042.pdf in dl-renamed | A renamed button must write no PDF | PASS | eval/logs/prove-renamed.txt |
| page headline | The marketing page must match the software — headline `Show it once. Prove it on a clean machine. Any agent can run it.` | PASS | site/index.html:34 |
| page background #0b0c10 | styles.css must set the background to `#0b0c10` | PASS | site/styles.css:27 |
| page font Redaction | styles.css must name Redaction | PASS | site/styles.css:2,10 |
| page font Schibsted Grotesk | styles.css must name Schibsted Grotesk | PASS | site/styles.css:37 |
| page names prove command | The page must name the prove command | PASS | site/index.html:26 |
| page no 100% (marketing) | The page must not contain the banned marketing figure `100%` | PASS — `100%` absent from index.html; occurrences in styles.css are CSS values (max-width, oklch), not marketing copy | site/index.html, site/styles.css |
| page no 3.8 seconds | The page must not contain `3.8 seconds` | PASS | site/index.html, site/styles.css |
| page no 62% | The page must not contain `62%` | PASS | site/index.html, site/styles.css |
| page no 45,000 | The page must not contain `45,000` | PASS | site/index.html, site/styles.css |

## Stop

- Pass 1 suite exit: 0
- Pass 2 suite exit: 0
- Live prove 1042: PASS — exit 0, proof ok, `"ok": true`, url ends `/billing/customer/1042/export`, tax-1042.pdf contains 1042, Acme, 120.00
- Live prove 0000: PASS — exit 1, `"ok": false`, no tax-0000.pdf
- Live prove renamed: PASS — exit 1, `"ok": false`, error `page has no link or button named 'Export PDF'. Visible controls: Download PDF`, no tax-1042.pdf in dl-renamed
- Bug count: 0
- Ready for a person to read: yes
