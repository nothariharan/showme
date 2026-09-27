# Tester

Ran on local `main` after `prove` and `site` were merged.

Command, from the showme repo root:

```
python -W default -m unittest discover -s tests -v
```

Exit code: 0. 28 tests, OK.

The page at `site/index.html`, served on http://127.0.0.1:8766/, shows the headline "Show it once. Prove it on a clean machine. Any agent can run it." and the `python -m showme prove` install line. Protocol navigation lands on `#protocol`. The wordmark and the Watch / Prove / Approve / Pack diagram load.

State: done
