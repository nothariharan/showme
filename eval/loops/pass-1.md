# Pass 1

## Environment

```
Python 3.12.10
C:\Users\HARIHARAN\AppData\Local\Programs\Python\Python312\python.exe
```

## Commands and exit codes

| Step | Command | Exit |
| --- | --- | --- |
| env | `python --version` | 0 |
| env | `python -c "import sys; print(sys.executable)"` | 0 |
| suite | `python -W default -m unittest discover -s tests -v` | 0 |
| validate | `python -m showme validate examples/export-customer-pdf/demonstration.json` | 0 |
| compile-1042 | `python -m showme compile examples/export-customer-pdf/demonstration.json --out eval/logs/skills-1042` | 0 |
| prove-1042 | `python -m showme prove eval/logs/skills-1042/export-customer-pdf --download-dir eval/logs/dl-1042 --set customer_id=1042 --set portal_url=http://127.0.0.1:55291` | 0 |
| prove-0000 | `python -m showme prove eval/logs/skills-1042/export-customer-pdf --download-dir eval/logs/dl-0000 --set customer_id=0000 --set portal_url=http://127.0.0.1:63978` | 1 |
| prove-renamed | `python -m showme prove eval/logs/skills-1042/export-customer-pdf --download-dir eval/logs/dl-renamed --set customer_id=1042 --set portal_url=http://127.0.0.1:60083` | 1 |
| page-check | Read `site/index.html` and `site/styles.css` | N/A |

## Notes

- `showme` package was not pip-installed; `python -m pip install -e .` was run first (no product code changed).
- Each portal was started in the background via `Start-Process`, port read from a temp file, then stopped with `Stop-Process` after prove returned.
- Suite exit 0, Ran 28 tests, OK.
- All three live prove commands matched their expected results.
- All page checks passed.
