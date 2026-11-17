# Login Scenarios — Provider Office Admin

**Page:** https://uat.assistme.me/login  
**Role under test:** Provider Office Admin only  
**Fields:** Mobile/Email ID, Password, Login button  

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Positive / Happy | 3 | TC-L01 – TC-L03 |
| Negative | 12 | TC-L04 – TC-L15 |
| **Total** | **15** | |

---

## Positive / Happy path

| ID | Title | Steps (high level) | Expected result |
|----|--------|--------------------|-----------------|
| TC-L01 | Valid login with correct email and password | Enter valid email + valid password → Login | User lands in the app; Provider Office Admin role is visible |
| TC-L02 | Valid login with correct mobile and password | Enter valid mobile + valid password → Login | User lands in the app; Provider Office Admin role is visible |
| TC-L03 | Password field masks input | Type password | Password characters are hidden (not shown as plain text) |

---

## Negative — wrong credentials

| ID | Title | Steps (high level) | Expected result |
|----|--------|--------------------|-----------------|
| TC-L04 | Invalid email | Enter wrong email + valid password → Login | Error shown; user stays on login page |
| TC-L05 | Invalid password | Enter valid email + wrong password → Login | Error shown; user stays on login page |
| TC-L06 | Invalid email and invalid password | Enter wrong email + wrong password → Login | Error shown; user stays on login page |
| TC-L07 | Unregistered mobile number | Enter unknown mobile + any password → Login | Error shown; user stays on login page |

---

## Negative — empty / missing fields

| ID | Title | Steps (high level) | Expected result |
|----|--------|--------------------|-----------------|
| TC-L08 | Empty email / mobile | Leave Mobile/Email empty → enter password → Login | Validation / error; login does not succeed |
| TC-L09 | Empty password | Enter valid email → leave password empty → Login | Validation / error; login does not succeed |
| TC-L10 | Both fields empty | Leave email and password empty → Login | Validation / error; login does not succeed |

---

## Negative — case sensitivity & format

| ID | Title | Steps (high level) | Expected result |
|----|--------|--------------------|-----------------|
| TC-L11 | Case-sensitive password | Enter valid email + password with wrong letter case → Login | Error shown; login fails (if password is case-sensitive) |
| TC-L12 | Case variation of email | Enter same email with different letter case → Login | Pass or fail based on real app behavior — document actual result |
| TC-L13 | Email with leading / trailing spaces | Enter valid email with spaces around it + valid password → Login | Pass or fail based on real app behavior — document actual result |
| TC-L14 | Password with leading / trailing spaces | Enter valid email + password with spaces around it → Login | Pass or fail based on real app behavior — document actual result |

---

## Negative — extra checks

| ID | Title | Steps (high level) | Expected result |
|----|--------|--------------------|-----------------|
| TC-L15 | SQL / script-like input in email field | Enter special/script text in email + any password → Login | Error or safe rejection; no crash; stays on login |

---

## Automation status

All 15 IDs are in `test_data/login_users.json` and collected by `tests/test_login.py`.

| ID | Notes |
|----|--------|
| TC-L02 | Needs `LOGIN_MOBILE` in `.env`; skipped if empty |
| TC-L03 | Asserts password input `type="password"` (no login submit) |
| TC-L12 | Email case variation → **success** (case-insensitive email) |
| TC-L13 | Email leading/trailing spaces → **success** (standard: trim). Marked `xfail` until UAT trims. |
| TC-L14 | Password leading/trailing spaces → **error** (standard: do not trim password) |

## Notes

- Negative cases assert the UAT error text from `error_message` / `error_messages` in `login_users.json` (plus “Welcome Back”).
- Automate **Provider Office Admin** credentials only for now (from `.env`).
- Locators: simple only — `get_by_role`, `get_by_label`, `page.locator("#id")`.
- Assertions: simple only — `to_be_visible`, `to_have_text`, `to_have_title`, `to_have_attribute` (see `APPROACH.md`).

---

## Suggested first automation set (when we start coding)

Priority smoke / core:

1. TC-L01 — valid login (happy path)  
2. TC-L05 — invalid password  
3. TC-L08 — empty email / mobile  
4. TC-L09 — empty password  
5. TC-L10 — both empty  

Then add the rest as regression.
