# Test reporting & failure debugging

Every pytest run (via `pytest.ini` defaults) produces:

| Artifact | Path | When |
|----------|------|------|
| HTML report | `reports/report.html` | Always |
| Failure screenshot (custom) | `reports/screenshots/<test>.png` | On test failure |
| Screenshot in HTML | Embedded / linked in the HTML report | On test failure |
| Playwright screenshot | `reports/test-results/` | On failure (`--screenshot=only-on-failure`) |
| Playwright trace | `reports/test-results/` | On failure (`--tracing=retain-on-failure`) |

## How to run

```powershell
python -m pytest tests
```

Or with an explicit report path (already default):

```powershell
python -m pytest tests --html=reports/report.html --self-contained-html
```

## How to debug a failure

1. Open `reports/report.html` in a browser  
2. Open the failed test — screenshot is attached  
3. Open the matching PNG under `reports/screenshots/`  
4. Optional: open the Playwright **trace** from `reports/test-results/` with:

```powershell
playwright show-trace reports/test-results/<folder>/trace.zip
```

## Smoke / markers

```powershell
python -m pytest tests -m smoke
python -m pytest tests -m e2e
python -m pytest tests -m regression
```
