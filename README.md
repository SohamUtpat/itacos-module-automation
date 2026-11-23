# Itacos Module Automation

Playwright + Pytest automation for the Assist Me / Itacos UAT app, focused on **Provider Office Admin** flows.

UI tests live in `tests/`. Login and Units API tests live in `api/`. The two suites share Pytest, Playwright, `.env`, and pytest-html, and they are run separately.

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
| Playwright APIRequestContext | Login API requests |

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
├── conftest.py         # UI auth, soft/hard page reset, failure screenshots
├── api/                # Login + Units API automation
│   ├── clients/api_client.py
│   ├── endpoints/auth_endpoints.py
│   ├── endpoints/unit_endpoints.py
│   ├── helpers/checks.py
│   ├── tests/test_login_api.py
│   ├── tests/test_units_api.py
│   ├── LOGIN_API_SCENARIOS.md
│   ├── UNITS_API_SCENARIOS.md
│   ├── test_data/login_data.json
│   ├── test_data/unit_data.json
│   ├── schemas/login_response_schema.json
│   ├── schemas/unit_create_response_schema.json
│   ├── schemas/unit_list_response_schema.json
│   └── conftest.py
├── pytest.ini          # Markers, report defaults
├── requirements.txt
├── .env.example        # Placeholder variable names
└── .env                # Local credentials (not committed)
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

API_BASE_URL=https://uat.assistme.me
API_USERNAME=your_test_username
API_PASSWORD=your_test_password
API_MOBILE=your_mobile_number
API_MAX_RESPONSE_MS=5000
API_BRANCH_CODE=SP-B008
API_UNIT_PASSWORD=Unit@12345
```

Copy `.env.example` if you want the same placeholders. `.env` is listed in `.gitignore`. Do not commit usernames, passwords, or tokens.

If `API_USERNAME` / `API_PASSWORD` are empty, the login API tests use `LOGIN_EMAIL_OR_MOBILE` and `LOGIN_PASSWORD`. `API_BASE_URL` falls back to the host of `BASE_URL`. Units API tests use `API_BRANCH_CODE` (default `SP-B008`) and `API_UNIT_PASSWORD` (default `Unit@12345`).

---

## How to run tests

### All UI tests

```powershell
python -m pytest tests/ -v
```

### Login API tests

```powershell
python -m pytest api/tests/test_login_api.py -v
```

### Units API tests

```powershell
python -m pytest api/tests/test_units_api.py -v
```

### All UI and API tests

```powershell
python -m pytest -v
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

The same `pytest.ini` options write `reports/report.html` for UI and API runs. To keep a UI report while running the login API, pass a second path:

```powershell
python -m pytest api/tests/test_login_api.py -v --html=reports/api-report.html --self-contained-html
```

Open the HTML report in a browser after a run. For a failed UI test, open the matching screenshot or view the Playwright trace:

```powershell
playwright show-trace reports/test-results/<folder>/trace.zip
```

More detail: [REPORTING.md](REPORTING.md)

---

## Login API

The login API suite calls the confirmed UAT endpoint:

`POST /user-management-service/v1/login`

Request fields are `userName`, `password`, `appType` (`WEB`), and `forceLogin` (`true`). A successful login returns HTTP 201 and `Login Successfully`. The token is at `data.loginAudit.token`. The user object is `data.loginAudit.userBasicDetails` (this is the live field name).

### Bearer token

`authenticated_api` in `api/conftest.py` logs in once per pytest session, reads `data.loginAudit.token`, and creates a second Playwright request context with `Authorization: Bearer <token>`, plus `x-tenant-id` and `user-id` from the same login response. The token is not printed and is disposed of when the session ends. Negative login tests use `api_client` and do not need that token.

Unit and admin-service calls need `x-tenant-id`. The login request itself is public.

---

## Units API

The units API suite covers the confirmed UAT endpoints for Service Provider Units:

| Action | Method / path |
|--------|----------------|
| Create | `POST /user-management-service/v1/user/itaco-user` |
| Update | `PUT /user-management-service/v1/user/itaco-user/{id}` |
| List / search | `GET /admin-service/v1/provider-units` |
| Delete (deactivate) | `DELETE /admin-service/v1/provider-unit/{id}` |

Create returns HTTP 201 and `ITACO User Created Successfully`. List returns `All Service Units Fetched Successfully`. Delete soft-deactivates with `Service Unit Is Deactivated`. Full cases: [api/UNITS_API_SCENARIOS.md](api/UNITS_API_SCENARIOS.md).

Office, branch, and workshop APIs beyond the unit prerequisites are not automated yet.

### Login API coverage

Implemented in `api/tests/test_login_api.py`:

- Valid username/password, HTTP 201, success message, token, user id, tenant id, first and last name
- User type `SERVICE_PROVIDER`, role `Provider Office Admin`, department `Service Providers`
- Permissions `View`, `Write`, and `Modify` for this test account only
- JSON content type, required response paths, and response time (`API_MAX_RESPONSE_MS`, default 5000)
- Username letter-case variation and mobile login (mobile is skipped when `API_MOBILE` / `LOGIN_MOBILE` is empty)
- Invalid, empty, missing, and null credentials
- Invalid email-shaped username, wrong password case, username spaces, invalid `appType`, invalid `forceLogin`
- Password is absent from the success body
- SQL-like and script-like usernames are rejected and do not return a token
- Five repeated invalid attempts stay HTTP 404. UAT did not return HTTP 429 during discovery

### UI scenario mapping

| UI case | API coverage |
|---------|----------------|
| TC-L01 valid email login | `test_login_with_valid_username_and_password` and the field checks on that response |
| TC-L02 valid mobile login | `test_login_with_valid_mobile` |
| TC-L03 password masking | UI only. The API checks that the password is not returned |
| TC-L04 invalid email | `invalid_username` |
| TC-L05 invalid password | `invalid_password` |
| TC-L06 both invalid | `both_credentials_invalid` |
| TC-L07 unknown mobile | Covered by the unknown-username rejection. A separate unknown-mobile case is not duplicated |
| TC-L08 empty username | `empty_username` |
| TC-L09 empty password | `empty_password` |
| TC-L10 both empty | `both_fields_empty` |
| TC-L11 password case | `password_wrong_case` |
| TC-L12 email case | `test_login_with_username_case_variation` |
| TC-L13 username spaces | `username_with_spaces`. UAT rejects the spaced username with HTTP 404 |
| TC-L14 password spaces | Not a separate API case. Wrong-password rejection is covered |
| TC-L15 SQL-like input | `test_sql_like_username_is_rejected` |

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
| Login API | [api/LOGIN_API_SCENARIOS.md](api/LOGIN_API_SCENARIOS.md) |
| Units API | [api/UNITS_API_SCENARIOS.md](api/UNITS_API_SCENARIOS.md) |
| Office | [OFFICE_SCENARIOS.md](OFFICE_SCENARIOS.md) |
| Branches | [BRANCHES_SCENARIOS.md](BRANCHES_SCENARIOS.md) |
| Units | [UNITS_SCENARIOS.md](UNITS_SCENARIOS.md) |
| Workshops | [WORKSHOPS_SCENARIOS.md](WORKSHOPS_SCENARIOS.md) |
| Plan | [MODULES_AUTOMATION_PLAN.md](MODULES_AUTOMATION_PLAN.md) |
