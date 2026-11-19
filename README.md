# Itacos Module Automation

Playwright + Pytest UI automation for the Assist Me / Itacos UAT app, focused on **Provider Office Admin** flows:

- Login
- Office Details
- Office Branches
- Units
- Cross-module E2E (Office → Branch → Unit)

**App:** https://uat.assistme.me/login

---

## Tech stack

| Tool | Purpose |
|------|---------|
| Python | Test runtime |
| Pytest | Test runner |
| Playwright | Browser automation |
| pytest-playwright | Playwright fixtures |
| python-dotenv | Load credentials from `.env` |
| pytest-html | HTML test report |

---

## Project structure

```
├── pages/              # Page objects (locators + actions only)
│   ├── login_page.py
│   ├── office_page.py
│   ├── branches_page.py
│   ├── units_page.py
│   └── sidebar.py
├── tests/              # Scenarios + assertions
│   ├── test_login.py
│   ├── test_office.py
│   ├── test_branches.py
│   ├── test_units.py
│   └── test_office_branch_unit_e2e.py
├── helpers/            # Shared helpers (URLs, unique data, location)
├── test_data/          # JSON test data
├── reports/            # HTML report, screenshots, traces
├── conftest.py         # Auth fixtures, failure screenshots
├── pytest.ini          # Markers, report defaults
├── requirements.txt
└── .env                # Local credentials
```

---

## Prerequisites

- Python 3.10+
- Git
- Access to UAT with a Provider Office Admin account

---

## Setup

### 1. Clone the repo

```powershell
git clone https://github.com/SohamUtpat/itacos-module-automation.git
cd itacos-module-automation
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
BASE_URL=https://uat.assistme.me/login
LOGIN_EMAIL_OR_MOBILE=your_email@example.com
LOGIN_MOBILE=your_mobile_number
LOGIN_PASSWORD=your_password
```

---

## How to run tests

### All tests

```powershell
python -m pytest tests
```

### By marker

```powershell
python -m pytest tests -m smoke
python -m pytest tests -m regression
python -m pytest tests -m e2e
```

### By module

```powershell
python -m pytest tests/test_login.py
python -m pytest tests/test_office.py
python -m pytest tests/test_branches.py
python -m pytest tests/test_units.py
python -m pytest tests/test_office_branch_unit_e2e.py
```

### Headed browser (optional)

```powershell
python -m pytest tests --headed
```

---

## Reports and debugging

Every run (via `pytest.ini`) produces:

| Artifact | Path |
|----------|------|
| HTML report | `reports/report.html` |
| Failure screenshots | `reports/screenshots/` |
| Playwright traces / artifacts | `reports/test-results/` |

Open the HTML report in a browser after a run. For a failed test, open the matching screenshot or view the Playwright trace:

```powershell
playwright show-trace reports/test-results/<folder>/trace.zip
```

More detail: [REPORTING.md](REPORTING.md)

---

## Coding approach

- **`pages/`** — simple locators and actions only (no assertions)
- **`tests/`** — scenarios and `expect(...)` assertions only
- Prefer `get_by_role`, `get_by_placeholder`, and simple CSS/`#id` locators
- Keep tests independent and clearly named

Full conventions: [APPROACH.md](APPROACH.md)

---

## Scenario docs

| Module | Doc |
|--------|-----|
| Login | [LOGIN_SCENARIOS.md](LOGIN_SCENARIOS.md) |
| Office | [OFFICE_SCENARIOS.md](OFFICE_SCENARIOS.md) |
| Branches | [BRANCHES_SCENARIOS.md](BRANCHES_SCENARIOS.md) |
| Units | [UNITS_SCENARIOS.md](UNITS_SCENARIOS.md) |
| Workshops | [WORKSHOPS_SCENARIOS.md](WORKSHOPS_SCENARIOS.md) |
| Plan | [MODULES_AUTOMATION_PLAN.md](MODULES_AUTOMATION_PLAN.md) |
