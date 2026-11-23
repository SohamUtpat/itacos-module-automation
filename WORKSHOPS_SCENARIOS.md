# Workshops Scenarios — Provider Office Admin

**List:** `/service-provider/garages`  
**Create:** `/service-provider/garages/create`  
**Update:** `/service-provider/garages/update/{id}`  
**Depends on:** Provider Office already onboarded (company name is shown on the form)  
**Tests:** `tests/test_workshops.py`  
**Run order:** Negative cases first, then smoke / positive.

The list has Code, Contact Email, City, Contact Number, Landline Number, Status, and Actions, plus a Map view switch. There is no visible search box, so this module has no search scenarios.

A successful create needs Select Brands, workshop type, Fuel Type, Priority, Repair Type, Mobile, Landline, Email, at least one working day, and a location (Country and Address). Shared values live in `test_data/workshop_cases.json` (Toyota, Mechanical, Petrol, priority 1, General Repair, location Katraj, Pune).

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Smoke | 1 | TC-W-SMOKE |
| Happy / Positive | 10 | TC-W01 – TC-W02, TC-W06 – TC-W13 |
| Negative | 5 | TC-W03 – TC-W05, TC-W14 – TC-W15 |

---

## Smoke

| ID | Title | Expected |
|----|--------|----------|
| TC-W-SMOKE | Workshops page loads | URL `/service-provider/garages`; heading **Workshops**; Create Workshop enabled; Map view visible; columns Code, Contact Email, City, Contact Number, Landline Number, Status, Actions |

---

## Happy / Positive

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-W01 | Create with required fields | Create Workshop → brand, workshop type, fuel, priority, repair type, mobile, email, landline, Mon–Fri with 24 Hours, location → Save → Confirm | Redirect to list; email row visible. Confirm text: "Are you sure you want to create workshop" |
| TC-W02 | Create with all fields | Required + alternative mobile, WhatsApp, alternative landline, Teams ID, PO Box → Save | Row visible in the grid |
| TC-W06 | Create shows row details | Create workshop → inspect the row | Code, city **Pune**, contact number, landline, and status **Active** visible |
| TC-W07 | Edit workshop | Create → Edit → change mobile → blur → Save → Confirm | Update URL `/service-provider/garages/update/{id}`; list shows the new mobile. Confirm text: "Are you sure you want to update workshop" |
| TC-W08 | Delete workshop | Create → Delete → Confirm | Dialog: "Are you sure you want to delete workshop." Email row and code cell are gone |
| TC-W09 | Map view toggle | Toggle Map view | Switch flips from its previous checked state |
| TC-W10 | Reset on create | Open create → fill mobile → Reset | Mobile is empty |
| TC-W11 | Working days custom (Mon–Wed) | Create with Monday, Tuesday, Wednesday only → Save | Row visible |
| TC-W12 | Confirm Cancel on create | Valid form → Save → Cancel | Stay on `/service-provider/garages/create`; no new row |
| TC-W13 | Delete Cancel | Create → Delete → Cancel | Row still visible |

---

## Negative

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-W03 | Empty required | Open create → Save with empty fields | Fuel type is Required; Mobile number is required; Landline number is required; Email is required.; Please select at least one day; Country is required; Address is required |
| TC-W04 | Alphabets in mobile | Mobile = `abcdefghij`, then leave the field | Please enter valid mobile number |
| TC-W05 | Invalid email | Valid mobile + email `bad-email` → Save | Enter a valid email. |
| TC-W14 | Invalid landline | Landline = `abcdefgh` → Save | Please enter valid Landline number |
| TC-W15 | No location | Fill contact, fuel, and days; skip location → Save | Country is required; Address is required |

---

## Reporting

Same as the other modules: `reports/report.html`, `reports/screenshots/`, `reports/test-results/`.
