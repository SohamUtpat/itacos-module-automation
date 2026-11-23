# Units API Scenarios — Provider Office Admin

**Create:** `POST /user-management-service/v1/user/itaco-user`  
**Update:** `PUT /user-management-service/v1/user/itaco-user/{id}`  
**List / search:** `GET /admin-service/v1/provider-units?page=1&size=20&search=&departmentId=`  
**Delete (deactivate):** `DELETE /admin-service/v1/provider-unit/{id}`  
**Branches (prerequisite):** `GET /admin-service/v1/provider-office-branches/{providerId}`  
**Provider office:** `GET /admin-service/v1/provider-office` (needs `user-id` header)  

**Role under test:** Provider Office Admin only  
**Auth headers:** `Authorization: Bearer <token>`, `x-tenant-id: <tenantId>`  
**Tests:** `api/tests/test_units_api.py`  
**Data:** `api/test_data/unit_data.json`

A successful create returns HTTP **201** and the message **ITACO User Created Successfully**. The unit user id is `data.itacoUserResponse.userBasicDetails.id`. The unit code is `unitCode` (for example `U248`).

Protected admin-service calls need `x-tenant-id` from the login response. Bearer alone is not enough for the units list on UAT.

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Create / response checks | 12 | TC-API-U01 – TC-API-U12 |
| List / search | 3 | TC-API-U13 – TC-API-U15 |
| Update / delete | 3 | TC-API-U16 – TC-API-U18 |
| Negative / security | 6 | TC-API-U19 – TC-API-U24 |
| **Total** | **24** | |

TC-API-U22 documents a UI vs API difference: the form requires a branch, but create without `branchId` currently returns HTTP 201 on UAT.

---

## Create / response checks

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-U01 | Create with required fields | First name, last name, email, phone, password, country `+91`, branch, role `Service Provider Unit` | HTTP 201 and message `ITACO User Created Successfully` |
| TC-API-U02 | HTTP status | Same valid create | Status code is 201 |
| TC-API-U03 | Success message | Same valid create | `message` is `ITACO User Created Successfully` |
| TC-API-U04 | Id and unit code | Same valid create | `userBasicDetails.id` and `unitCode` are non-empty |
| TC-API-U05 | Email and phone echoed | Same valid create | Response email and phone match the request |
| TC-API-U06 | Role | Same valid create | `role.role` is `Service Provider Unit` |
| TC-API-U07 | Department | Same valid create | `department.name` is `Service Providers` |
| TC-API-U08 | Status fields | Same valid create | `userStatus` / `unitStatus` are `ACTIVE`, `userType` is `SERVICE_PROVIDER` |
| TC-API-U09 | Branch link | Same valid create | `providerOfficeBranchResponse` matches the selected branch id and code |
| TC-API-U10 | Response structure | Same valid create | Required paths in `api/schemas/unit_create_response_schema.json` are present |
| TC-API-U11 | Content type | Same valid create | `Content-Type` contains `application/json` |
| TC-API-U12 | Response time | Same valid create | Elapsed time is within `API_MAX_RESPONSE_MS` (default 5000 ms) |

Each create also checks that the unit password is not returned in the body. Created units are deactivated at session end.

---

## List / search

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-U13 | List units | Authenticated GET provider-units | HTTP 200 and message `All Service Units Fetched Successfully` |
| TC-API-U14 | List schema | Same list call | Required list paths (and first-item paths when rows exist) are present |
| TC-API-U15 | Search by email | Create a unit, then search with the email local-part | Created email appears in `data.users` |

---

## Update / delete

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-U16 | Update first name | `PUT .../itaco-user/{id}` with `firstName=ApiEdited` | HTTP 200, message `ITACO User's Details are Updated Successfully`, first name updated |
| TC-API-U17 | Update language | `PUT` with `languageCode=en` | HTTP 200 and the same update success message |
| TC-API-U18 | Delete / deactivate | `DELETE /admin-service/v1/provider-unit/{id}` | HTTP 200 and message `Service Unit Is Deactivated` |

UI delete confirms in a dialog; the API call itself deactivates the unit (soft delete).

---

## Negative / security

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-U19 | Invalid email | `email=not-an-email` | HTTP 400. Error includes `Email is Invalid` |
| TC-API-U20 | Alphabetic phone | `phone=abcdefghij` | HTTP 400. Error includes `invalid.phone.number` |
| TC-API-U21 | Duplicate email | Reuse an existing unit email | HTTP 400. Error includes `already exists` |
| TC-API-U22 | Missing branchId | Omit `branchId` | HTTP 201 on current UAT (API does not enforce the UI branch-required rule). Password is not echoed. Revisit if the API starts rejecting this |
| TC-API-U23 | No auth token | Create without `Authorization` | HTTP 401 Unauthorized |
| TC-API-U24 | Bearer without tenant | List units with Bearer only | Not HTTP 200. UAT currently returns HTTP 500 `Something went wrong` |

---

## Create request shape

```json
{
  "userBasicDetailsPostRequest": {
    "firstName": "Rahul",
    "lastName": "Sharma",
    "password": "Unit@12345",
    "countryCode": "+91",
    "phone": "9876543210",
    "email": "api.unit.example@example.com",
    "userStatus": "ACTIVE",
    "userRolesPostRequest": [
      {
        "departmentName": "Service Providers",
        "role": [{ "role": "Service Provider Unit" }]
      }
    ]
  },
  "providerId": "<provider-office-id>",
  "branchId": "<branch-id>"
}
```

Default branch code is **SP-B008** (`API_BRANCH_CODE` overrides). Provider id is loaded from `GET /admin-service/v1/provider-office`.

---

## UI mapping

| UI scenario | API scenario |
|-------------|--------------|
| TC-U-SMOKE Units page loads | TC-API-U13 list success |
| TC-U01 / TC-U02 create | TC-API-U01 – TC-API-U12 |
| TC-U07 row details / code | TC-API-U04 unit code |
| TC-U15 Other Details language update | TC-API-U17 |
| TC-U08 edit first name | TC-API-U16 |
| TC-U09 delete | TC-API-U18 |
| TC-U10 search by email | TC-API-U15 |
| TC-U04 alphabetic phone | TC-API-U20 |
| TC-U05 invalid email | TC-API-U19 |
| TC-U03 empty required | Not mirrored. Empty create body returns HTTP 500 on UAT |
| TC-U16 no branch | TC-API-U22 documents that the API currently still creates without `branchId` |
| TC-U12 Map view, TC-U13 Reset, TC-U14 Delete Cancel | UI only |

---

## How to run

```powershell
python -m pytest api/tests/test_units_api.py -v
```

Optional env:

```env
API_BRANCH_CODE=SP-B008
API_UNIT_PASSWORD=Unit@12345
```
