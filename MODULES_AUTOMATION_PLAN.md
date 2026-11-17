# Automation plan: Office, Branches, Units

**App:** https://uat.assistme.me  
**Role:** Provider Office Admin  
**Rule:** Keep the same simple style as Login (`APPROACH.md`) — page actions + test assertions only.

---

## What we found on UAT

Logged in as Provider Office Admin → `/service-provider/dashboard`.

| Module (sidebar) | URL | What it is | Current state on this account |
|------------------|-----|------------|-------------------------------|
| **Office Details** | `/service-provider/provider-office/manage-office` | Provider Office Onboarding form | Mostly **empty**; Save / Reset present |
| **Office Branches** | `/service-provider/branches` | Grid list + Map view | **No rows**; no Create button visible |
| **Units** | `/service-provider/units` | Grid list + Search + Map view + Create Unit | **No rows**; **Create Unit disabled** |

### Office Details sections

Provider Details → Contact Details → Bank Details → Active Hours → Address Details (+ View History)

Address fields (Country, Area, City, Address, Lat/Long) are filled via **Search for a Location** (readonly until a location is picked).

### Table columns

| Units | Branches |
|-------|----------|
| Code | Code |
| Name | Contact Email |
| Email | City |
| Phone Number | Contact Number |
| Country | Landline Number |
| Status | Status |
| Actions | Actions |

### Dependency (important)

```
Login → Office Details → Office Branches → Units
```

Likely product rule: **office must exist → then branches → then units**.  
That fits empty lists and disabled Create Unit. Confirm with the team before locking create scenarios.

---

## How this fits our existing approach

Reuse patterns from Login and `APPROACH.md`:

- **Page objects** (`pages/`): simple locators + actions only (fill, click, navigate)
- **Tests** (`tests/`): scenarios + `expect(...)` only
- **Locators:** `get_by_role` / `get_by_label` / simple `#id`
- **Coverage:** smoke nav → happy path → positive → negative
- **Auth:** login via fixture using `.env` credentials (`authenticated_page`)

---

## Phases

### Phase 0 — Test data / unlock creates (blocker)

Before CRUD automation:

1. Confirm whether this UAT user should already have office + at least one branch.
2. If not: either manually complete Office onboarding + create one branch, **or** automate Office save first as the prerequisite E2E.
3. Re-check Units: Create Unit should become enabled once a branch exists.

Without this, Unit create tests cannot run.

### Phase 1 — Smoke (safe now, even with empty data)

For each module:

- Navigate from sidebar
- Assert heading / URL
- Assert table shell (column headers visible)
- Empty state: “No rows” / `0–0 of 0` (baseline, or update when seed data appears)

**Files to add later:**

- `pages/sidebar.py` (or dashboard helper)
- `pages/office_page.py`
- `pages/branches_page.py`
- `pages/units_page.py`
- `tests/test_office.py` (smoke + happy + negative)
- `tests/test_branches.py` (smoke + happy + negative)
- `tests/test_units.py` (smoke + happy + negative)
- `OFFICE_SCENARIOS.md`
- `BRANCHES_SCENARIOS.md`
- `UNITS_SCENARIOS.md`

### Phase 2 — Office Details (first CRUD module)

| Type | Examples |
|------|----------|
| Happy | Fill required fields → Save → success toast / data persists on reload |
| Positive | Edit existing office; View History opens |
| Negative | Save with empty Company Name / Email / required address → field errors |

**Required fields observed:** Company Name, Short Name, Network Type, Currency, Payable Days, Mobile, Email, Country, Address, Lat, Long (location search dependent).

Network Type options seen on UAT: Corporate Client Network, ITACO Network, Other.

### Phase 3 — Office Branches

Once create UI is available / unlocked:

| Type | Examples |
|------|----------|
| Happy | Create branch → appears in grid |
| Positive | Search/sort/status; Map view toggle |
| Negative | Missing required fields; duplicate rules (if any) |

Also cover Actions (edit / view / deactivate) once those menus are documented.

### Phase 4 — Units

Once Create Unit is enabled:

| Type | Examples |
|------|----------|
| Happy | Create unit → row in table with expected Name/Email/Phone |
| Positive | Search filters list; pagination; Map view |
| Negative | Create with empty required fields; Create Unit disabled when no branch |

---

## Shared test design

- **Auth fixture:** login once per test (or session) → yield page on dashboard
- **Navigate helper:** sidebar clicks for Units / Office Details / Office Branches
- **Test data:** JSON under `test_data/` (office / branch / unit payloads); unique names with timestamp
- **Cleanup:** delete/deactivate created records in teardown where UI allows; otherwise unique prefixes
- **Toasts:** assert with `.first` + longer timeout (toasts auto-dismiss)

---

## Suggested build order

1. Auth + sidebar navigation page object  
2. Smoke tests for Office / Branches / Units  
3. Scenario docs + capture exact validation/toast text from UAT  
4. Office save happy path + required-field negatives  
5. Branch create (after unlock)  
6. Unit create + search (after Create Unit enabled)  

---

## Assumption

Treat **Office → Branches → Units** as the dependency chain.  
Start coding with **smoke + Office**, then Branches / Units CRUD only after create actions are available on this account.

---

## Implemented (current)

- Auth fixture: `authenticated_page` in `conftest.py`
- Pages: `sidebar.py`, `office_page.py`, `branches_page.py`, `units_page.py`
- Smoke + happy (required/all) + negatives + E2E happy path
- Scenario docs: `OFFICE_SCENARIOS.md`, `BRANCHES_SCENARIOS.md`, `UNITS_SCENARIOS.md`
- Failure debugging: see `REPORTING.md` (HTML report + screenshots + traces)
