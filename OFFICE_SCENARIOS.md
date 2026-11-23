# Office Details Scenarios — Provider Office Admin

**Page:** `/service-provider/provider-office/manage-office`  
**Role:** Provider Office Admin  
**Note:** This screen is onboarding/edit for the office (not a multi-row create list).

**Run order:** Negative cases first, then smoke / positive.

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Negative | 7 | TC-O03 – TC-O05, TC-O13 – TC-O16 |
| Smoke | 1 | TC-O-SMOKE |
| Happy / Positive | 8 | TC-O01 – TC-O02, TC-O06 – TC-O12 |

---

## Negative

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-O03 | Empty company name | Clear Company Name → Save | Error: Company name is required |
| TC-O04 | Alphabets in mobile | Enter letters in Mobile → Save | Error: Please enter valid mobile number |
| TC-O05 | Invalid email | Enter `not-an-email` → Save | Error: Enter a valid email. |
| TC-O13 | Empty short name | Clear Short Name → Save | Error: Short name is required |
| TC-O14 | Empty email | Clear Email → Save | Error: Email is required. |
| TC-O15 | Empty mobile | Clear Mobile → Save | Error: Mobile number is required |
| TC-O16 | Invalid landline letters | Enter letters in Landline → Save | Validation error for landline (if enforced) |

---

## Smoke

| ID | Title | Expected |
|----|--------|----------|
| TC-O-SMOKE | Office Details page loads | Heading **Provider Office Onboarding**; Company Name + Save/Reset visible |

---

## Happy / Positive

| ID | Title | Steps | Expected |
|----|--------|-------|----------|
| TC-O01 | Save with required fields | Fill Company Name, Short Name, Mobile, Email, location → Save | Form stays populated; office saved |
| TC-O02 | Save with all fields | Required + Landline + Comments → Save | Values persist on form |
| TC-O06 | Save persists after reload | Save required → reload page | Company Name / Short Name still populated |
| TC-O07 | Update existing office comments | Change Comments → Save | Updated comments remain |
| TC-O08 | Save Bank Details | Fill Account Number, IBAN, Branch → Save | Bank fields persist |
| TC-O09 | Active Hours section usable | Open Active Hours → toggle Saturday | Section visible; day checkbox state changes |
| TC-O10 | Network Type / Currency visible | Open Office Details | Network Type + Currency comboboxes visible; Payable Days shown |
| TC-O11 | View History | Click View History | History dialog / panel opens |
| TC-O12 | Reset restores unsaved change | Change Comments → Reset | Comments restored to previous saved value |

---

## Reporting

Failed tests write:

- HTML report: `reports/report.html`
- Screenshot: `reports/screenshots/<test-id>.png` (attached in HTML)
- Playwright artifacts: `reports/test-results/` (screenshot + trace on failure)
