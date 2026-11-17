# Assist Me Automation — Approach

**App:** https://uat.assistme.me/login  
**First role:** Provider Office Admin only  
**Rule:** Keep code simple, clean, and easy to understand.

---

## How we write code (agreed)

### Page files (`pages/`)
- Only **simple locators** and **actions** (fill, click, navigate)
- No big methods, no heavy logic
- No assertions here

### Test files (`tests/`)
- Only **test scenarios** and **assertions**
- Call page actions, then check the result with `expect(...)`
- Keep each test easy to read

### Locators (keep simple)
Prefer only these:

| Style | Example |
|-------|---------|
| `get_by_role` | `page.get_by_role("button", name="login")` |
| `get_by_placeholder` | `page.get_by_placeholder("Password")` |
| `page.locator` with id / simple CSS | `page.locator("#email")` or `page.locator("[data-test='error']")` |

Avoid complex chained / XPath locators unless there is no simple option.

### Assertions (keep simple)
Prefer only these web-first checks:

| Assertion | Use for |
|-----------|---------|
| `expect(...).to_be_visible()` | Element is on screen |
| `expect(...).to_have_text("...")` | Exact text (error message, label) |
| `expect(...).to_have_title("...")` | Page title |
| `expect(...).to_have_value("...")` | Input field value (when needed) |

Example style:

```python
expect(page.get_by_role("heading", name="Welcome Back")).to_be_visible()
expect(page).to_have_title("Assist Me")
expect(error).to_have_text("exact error text here")
```

### Style
- Small files
- Clear names
- Reuse the same patterns you learned in Python / Pytest / Playwright — only what we choose to use

*(Exact file names and folder layout will be decided when you say how to write them.)*

---

## Modules (in order)

1. **Login** — Provider Office Admin only  
2. **Office**  
3. **Units**  
4. **Office Branches**

---

## How we test (agreed)

Test each module **neatly** — clear scenarios, one purpose per test — and cover:

| Type | Meaning | Example |
|------|---------|---------|
| **Happy path (E2E)** | Full success flow start to finish | Login → open Units → create unit → see it in the table |
| **Positive** | Valid input / allowed action works | Correct credentials; required fields filled; create succeeds |
| **Negative** | Invalid / missing input is rejected | Wrong password; empty required field; error message shown |

### Rules for scenarios
- Keep tests **independent** where possible (one scenario = one clear check)
- Name tests so the intent is obvious (`test_login_with_valid_credentials`, `test_login_with_wrong_password`)
- Assertions stay in the **test** file
- End-to-end happy paths connect modules in order when needed (e.g. office ready → then unit → then branch)
- Positive + negative cases cover the important validations on each screen

### Starting point for Login
- Positive / happy: valid Provider Office Admin login → lands in app  
- Negative: wrong password, empty email/password (exact cases we confirm on UI)

*(Full scenario lists for Office / Units / Branches will be written when we reach each module.)*

---

## Opinion: which path should we use?

### Option A — Login as existing Provider Office Admin (recommended now)
1. Open login page  
2. Login with the Provider Office Admin you already created  
3. Automate Office → Units → Branches  

**Why this is better first**
- Matches your goal: automate those three modules  
- Simpler and more stable (no create-user / invite / approval steps)  
- Faster to learn and debug  
- Same style as your Sauce Demo practice: login with known user, then test features  

### Option B — Main/Admin creates Provider Office Admin, then login
1. Login as main/admin  
2. Create a Provider Office Admin  
3. Logout / login as that new user  
4. Then create Office, Units, Branches  

**When this makes sense later**
- Full end-to-end “onboarding” coverage  
- After Option A is stable  

**Why not first**
- Longer, more moving parts, easier to flake  
- Needs admin credentials + create-user UI details  
- Mixes two roles before the three modules are solid  

---

## Decision (suggested)

**Start with Option A.**  
Use the Provider Office Admin account you already have.  
Add “create Provider Office Admin from main admin” later as a separate flow.

---

## Next (when you say)

- You decide file/folder names and what to reuse from the learning project  
- Then we write the simple login page + login test only  
