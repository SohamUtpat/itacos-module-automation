# Units Scenarios — Provider Office Admin

**List:** `/service-provider/units`  
**Create:** `/service-provider/units/create`  
**Update:** `/service-provider/users/update/{id}`  
**Depends on:** at least one Branch (e.g. SP-B008)  

**Run order:** Negative cases first, then smoke / positive.

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Negative | 5 | TC-U03 – TC-U06, TC-U17 |
| Smoke | 1 | TC-U-SMOKE |
| Happy / Positive | 12 | TC-U01 – TC-U02, TC-U07 – TC-U16 |
| E2E happy path | 3 | TC-E2E-01 – TC-E2E-03 |

---

## Negative

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-U03 | Empty required | Open create → Submit empty | Errors: First Name / Email / Country code / Phone / Password / Confirm password is required. |
| TC-U04 | Alphabets in phone | Phone = letters → Submit | Error: Enter a valid phone number. |
| TC-U05 | Invalid email | Email = `not-an-email` → Submit | Error: Enter a valid email. |
| TC-U06 | Password mismatch | Confirm Password different → Submit | Error: Passwords do not match. |
| TC-U17 | Weak / short password | Password = `123` → Submit | Password validation error (if enforced) |

---

## Smoke

| ID | Title | Expected |
|----|--------|----------|
| TC-U-SMOKE | Units page loads | Heading **Units**; Create Unit enabled; Search + Actions column visible |

---

## Happy / Positive

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-U01 | Create with required fields | First Name, Email, Country Code, Phone, Password, Confirm, Branch → Submit → Back | Toast **user created successfully**. Other Details opens with Submit disabled. Back shows the new email row |
| TC-U02 | Create with all fields | Required + Last Name → Submit → Back | Toast **user created successfully** and the row is visible |
| TC-U07 | Create shows row details | Create unit → Back → inspect row | Toast **user created successfully**. Code is visible with the email |
| TC-U15 | Update from Other Details | Create → set Language = English → Submit | Toast **ITACO User's Details are Updated Successfully**. Same email row is on the list |
| TC-U08 | Edit unit | Create → Edit → change First Name → Submit | Updated name visible in grid |
| TC-U09 | Delete unit | Create → Delete → Confirm | Row gone |
| TC-U10 | Search by email | Create → Search email fragment | Matching row visible; count reduced |
| TC-U11 | Clear search | Search then clear | Full list / original row still findable |
| TC-U12 | Map view toggle | Toggle Map view | Switch checked |
| TC-U13 | Reset on create | Open create → fill First Name → Reset | First Name cleared |
| TC-U14 | Delete Cancel | Create → Delete → Cancel | Row still visible |
| TC-U16 | Create without branch | Fill personal fields, skip Branch → Submit → Back | Toast **user created successfully**; email row visible (branch is optional) |

---

## E2E happy path

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-E2E-01 | Office → Branch → Unit | Save office → create branch → create unit with new branch code | Branch email + unit email both visible in grids |
| TC-E2E-02 | Branch → Unit → Edit → Search | Create branch + unit → edit unit name → search finds it | Updated name visible via search |
| TC-E2E-03 | Create Unit enabled with branches | Open Units when branches exist | Create Unit enabled |

---

## Reporting

Same as Office: `reports/report.html`, `reports/screenshots/`, `reports/test-results/`.
