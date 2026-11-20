# Login API Scenarios — Provider Office Admin

**Endpoint:** `POST https://uat.assistme.me/user-management-service/v1/login`  
**Role under test:** Provider Office Admin only  
**Request fields:** `userName`, `password`, `appType` (`WEB`), `forceLogin` (`true`)  
**Tests:** `api/tests/test_login_api.py`  
**Data:** `api/test_data/login_data.json`

A successful login returns HTTP **201** and the message **Login Successfully**. The token is `data.loginAudit.token`. User details are under `data.loginAudit.userBasicDetails`.

Role, department, and permissions below are for the configured Provider Office Admin account. Other users can differ.

---

## Summary

| Type | Count | IDs |
|------|-------|-----|
| Positive / response checks | 16 | TC-API-L01 – TC-API-L16 |
| Negative | 15 | TC-API-L17 – TC-API-L31 |
| Security | 5 | TC-API-L32 – TC-API-L36 |
| **Total** | **36** | |

---

## Positive / response checks

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-L01 | Valid username and password | Configured username + password, `appType=WEB`, `forceLogin=true` | HTTP 201 and message `Login Successfully` |
| TC-API-L02 | HTTP status | Same valid login | Status code is 201 |
| TC-API-L03 | Success message | Same valid login | `message` is `Login Successfully` |
| TC-API-L04 | Token generated | Same valid login | `data.loginAudit.token` is a non-empty string |
| TC-API-L05 | User id | Same valid login | `userBasicDetails.id` is present |
| TC-API-L06 | Tenant id | Same valid login | `userBasicDetails.tenantId` is present |
| TC-API-L07 | First and last name | Same valid login | `firstName` and `lastName` are present |
| TC-API-L08 | User type | Same valid login | `userType` is `SERVICE_PROVIDER` |
| TC-API-L09 | Role | Same valid login | `role.role` is `Provider Office Admin` |
| TC-API-L10 | Department | Same valid login | `userRolesPostResponse` includes department `Service Providers` |
| TC-API-L11 | Permissions | Same valid login | Permission names are `View`, `Write`, and `Modify` |
| TC-API-L12 | Response structure | Same valid login | Required paths in `api/schemas/login_response_schema.json` are present |
| TC-API-L13 | Content type | Same valid login | `Content-Type` contains `application/json` |
| TC-API-L14 | Response time | Same valid login | Elapsed time is within `API_MAX_RESPONSE_MS` (default 5000 ms) |
| TC-API-L15 | Username letter case | Same username with swapped letter case + valid password | HTTP 201, success message, and a token |
| TC-API-L16 | Valid mobile | `API_MOBILE` or `LOGIN_MOBILE` + valid password | HTTP 201, success message, and a token. Skipped when no mobile is set |

TC-API-L01 through TC-API-L14 share one login response for the session.

---

## Negative — wrong credentials

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-L17 | Invalid username | `wrong.user@example.com` + valid password | HTTP 404. `Invalid username or Password for wrong.user@example.com`. No token |
| TC-API-L18 | Invalid password | Valid username + `WrongPassword123` | HTTP 400. `Invalid username or Password `. No token |
| TC-API-L19 | Both credentials invalid | `wrong.user@example.com` + `WrongPassword123` | HTTP 404. Same unknown-username message. No token |

---

## Negative — empty, missing, and null fields

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-L20 | Empty username | `userName=""` + valid password | HTTP 400. `Either Email or Phone Number is Mandatory` |
| TC-API-L21 | Empty password | Valid username + `password=""` | HTTP 400. `Password is Mandatory` |
| TC-API-L22 | Both fields empty | `userName=""` and `password=""` | HTTP 400. Both mandatory messages |
| TC-API-L23 | Missing username field | Body has no `userName` | HTTP 400. `Either Email or Phone Number is Mandatory` |
| TC-API-L24 | Missing password field | Body has no `password` | HTTP 400. `Password is Mandatory` |
| TC-API-L25 | Null username | `userName=null` | HTTP 400. `Either Email or Phone Number is Mandatory` |
| TC-API-L26 | Null password | `password=null` | HTTP 400. `Password is Mandatory` |

---

## Negative — format and extra fields

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-L27 | Invalid email format | `userName=not-an-email` | HTTP 404. Treated as an unknown username, not a separate format error |
| TC-API-L28 | Incorrect password case | Valid username + password with swapped letter case | HTTP 400. `Invalid username or Password ` |
| TC-API-L29 | Username with leading and trailing spaces | Valid username wrapped in spaces + valid password | HTTP 404. Message includes the spaced username. UAT does not trim it |
| TC-API-L30 | Invalid appType | `appType=NOT_A_REAL_APP` | HTTP 400. `App type not Valid. Only Mobile and Web are allowed` |
| TC-API-L31 | Invalid forceLogin | `forceLogin="yes"` | HTTP 400. Body error is `Bad Request` |

Every negative case also checks that the response is JSON, the password is not echoed, and the body does not contain a server stack trace.

---

## Security

| ID | Title | Request | Expected result |
|----|--------|---------|-----------------|
| TC-API-L32 | Password is not returned | Valid login response | Password value is absent, and there is no `password` field |
| TC-API-L33 | SQL-like username | `userName=' OR '1'='1` | HTTP 404 and the invalid-username message. No token |
| TC-API-L34 | Script-like username | `userName=<script>alert(1)</script>` | HTTP 404, JSON rather than HTML, and no token |
| TC-API-L35 | Repeated invalid logins | Five attempts with `rate.limit.probe@example.com` | Each attempt is HTTP 404. UAT did not return 429 for these five calls |
| TC-API-L36 | Bearer header on the authenticated client | Login once, then build the authenticated client | `Authorization` starts with `Bearer ` and includes the login token |

Invalid-credential cases also confirm that a rejected login does not return `data.loginAudit.token`.

These checks wait for a confirmed protected endpoint:

- Expired token is rejected
- Modified token is rejected
- A request with no token cannot call a protected endpoint

The login URL is public, so those three checks are not part of this file yet.

---

## UI mapping

| UI scenario | API scenario |
|-------------|--------------|
| TC-L01 valid email login | TC-API-L01 – TC-API-L14 |
| TC-L02 valid mobile login | TC-API-L16 |
| TC-L03 password masking | UI only. API equivalent is TC-API-L32 |
| TC-L04 invalid email | TC-API-L17 |
| TC-L05 invalid password | TC-API-L18 |
| TC-L06 both invalid | TC-API-L19 |
| TC-L07 unknown mobile | Same rejection as an unknown username (TC-API-L17) |
| TC-L08 empty email / mobile | TC-API-L20 |
| TC-L09 empty password | TC-API-L21 |
| TC-L10 both empty | TC-API-L22 |
| TC-L11 password case | TC-API-L28 |
| TC-L12 email case | TC-API-L15 |
| TC-L13 email with spaces | TC-API-L29 |
| TC-L14 password with spaces | No separate API case |
| TC-L15 SQL-like input | TC-API-L33 |

---

## How to run

```powershell
python -m pytest api/tests/test_login_api.py -v
```
