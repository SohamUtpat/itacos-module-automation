# Office Branches Scenarios — Provider Office Admin

**List:** `/service-provider/branches`  
**Create:** `/service-provider/branches/create`  
**Update:** `/service-provider/branches/update/{id}`  
**Depends on:** Office Details saved  

**Run order:** Negative cases first, then smoke / positive.

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Negative | 6 | TC-B03 – TC-B05, TC-B13 – TC-B15 |
| Smoke | 1 | TC-B-SMOKE |
| Happy / Positive | 8 | TC-B01 – TC-B02, TC-B06 – TC-B12 |

---

## Negative

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-B03 | Empty required | Open create → Save with empty fields | Errors: Mobile number is required; Landline number is required; Email is required.; Please select at least one day |
| TC-B04 | Alphabets in mobile / invalid email | Mobile = letters, Email = `alpha.mail` → Save | Errors: Please enter valid mobile number; Enter a valid email. |
| TC-B05 | Invalid email | Valid mobile + `bad-email` → Save | Error: Enter a valid email. |
| TC-B13 | Duplicate email | Create branch → create again with same email | Duplicate / already exists error (if enforced) |
| TC-B14 | Invalid landline | Landline = letters → Save | Landline validation error (if enforced) |
| TC-B15 | No location | Fill contact + days, skip location → Save | Address / location required error (if enforced) |

---

## Smoke

| ID | Title | Expected |
|----|--------|----------|
| TC-B-SMOKE | Branches page loads | Heading **Branches**; Create Branch enabled; Code + Actions columns visible (Edit/Delete) |

---

## Happy / Positive

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-B01 | Create with required fields | Create Branch → Mobile, Email, Landline, Select Days, location → Save | Toast **Branch is created for Service Provider**; redirect to list; email row visible |
| TC-B02 | Create with all fields | Required + Alt mobile, WhatsApp, Teams ID, PO Box → Save | Toast **Branch is created for Service Provider**; row visible in grid |
| TC-B06 | Create shows row details | Create branch → inspect row | Toast **Branch is created for Service Provider**; City / Contact / Status (Active) visible |
| TC-B07 | Edit branch | Create → Edit → change mobile → Save | Create toast, then toast **Branch is updated for Service Provider**; updated mobile in grid |
| TC-B08 | Delete branch | Create → Delete → Confirm | Create toast, then toast **Branch Deleted Successfully**; row no longer visible |
| TC-B09 | Map view toggle | Toggle Map view switch | Switch checked; map area or alternate view shown |
| TC-B10 | Reset on create | Open create → fill mobile → Reset | Mobile cleared / restored empty |
| TC-B11 | Working days custom (Mon–Wed) | Create with Mon–Wed only + 24 Hours → Save | Toast **Branch is created for Service Provider**; row visible |
| TC-B12 | Confirm Cancel on create | Valid form → Save → Cancel on confirm | Stay on create form; no new row |

---

## Reporting

Same as Office: `reports/report.html`, `reports/screenshots/`, `reports/test-results/`.
