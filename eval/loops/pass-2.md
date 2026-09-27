# Pass 2

## Suite rerun

```
python -W default -m unittest discover -s tests -v
```

Exit: 0 — matches pass 1 (exit 0). `Ran 28 tests` and `OK`.

Full output: eval/logs/unittest-pass-2.txt

## Live prove reruns

No live prove commands failed in pass 1. No portal reruns were needed.

## Comparison with pass 1

| Check | Pass 1 | Pass 2 | Match |
| --- | --- | --- | --- |
| suite | PASS, exit 0 | PASS, exit 0 | yes |
| prove-1042 | PASS, exit 0 | not rerun (passed) | N/A |
| prove-0000 | PASS, exit 1 | not rerun (passed) | N/A |
| prove-renamed | PASS, exit 1 | not rerun (passed) | N/A |

Pass 2 confirms pass 1. No result flipped.
