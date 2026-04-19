# LeadwayHMO RxHub — Technical Specification for Claude Code

## Overview
Build a **PBM Member Self-Service Web Platform** with React frontend + FastAPI backend + PostgreSQL, integrated with the Leadway Health Prognosis PBM system via REST APIs.

---

## Architecture

```
Member Portal (React) ──→ FastAPI Backend ──→ Prognosis PBM APIs
Admin Portal (React)  ──→     ↕              PostgreSQL DB
                         ↕
                    Termii SMS (OTP)
                    AWS S3 (uploads)
```

---

## Prognosis API Integration (CRITICAL)

### Authentication
All Prognosis APIs require Bearer token authentication.

**Login:**
```
POST https://prognosis-api.leadwayhealth.com/api/ApiUsers/Login
Body: {"Username": "whatsappBot", "Password": "..."}
Response: Bearer token (cache for 55 minutes)
```

### Member APIs

**Validate Member (Login):**
```
GET /api/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={id}
Response: {"status": 200, "result": [{
  "Member_FirstName": "Favour",
  "Member_MemberUniqueID": 1738,
  "scheme": "MAX - Leadway Holdings2026",
  "Company": "LEADWAY ASSURANCE COMPANY LIMITED",
  "PhoneNumber": "08188626141",
  "EmailAdress": "favour.cabana@gmail.com",
  ...
}]}
```
- Unwrap `result[0]` from response envelope
- Phone comparison for login: normalize Nigerian formats (+234, 234, 0)

**Get Member Medications:**
```
GET /api/PharmacyDelivery/GetPbmMedication?enrolleeid={id}
Response: {"status": 200, "result": [{
  "EntryNo": 28582,
  "Medications": "HYPROMELLOSE EYE DROPS",
  "LastPackDate": "2025-09-01T15:18:00",
  "NextPackDate": "2025-09-01T00:00:00",
  "diagnosisname": "Dry eye syndrome",
  "PhoneNumber": "08188626141",
  "scheme": "MAX - Leadway Holdings2026",
  "Company": "LEADWAY ASSURANCE COMPANY LIMITED",
  "Address": "12 oshoala Street,Ikeja,Lagos",
  "pharmacyname": "PHARMACY BENEFIT PROGRAMME LAGOS",
  ...
}]}
```
- Key fields: `EntryNo` (unique ID), `Medications` (drug name), `LastPackDate`, `NextPackDate`
- Also contains member delivery info: phone, address, email, scheme, company

### Medication Search (Autocomplete)
```
GET /api/ListValues/GetProceduresByFilter_pbm?filtertype=0&providerid=8520&searchbyname={term}
Response: [{"tariff_desc": "Amlodipine 10mg (Sandoz)", "tariff_code": "C0810092E", "cost": 3500.0}]
```
- Field mapping: `tariff_desc` → drug name, `tariff_code` → procedure ID

### Diagnosis Search (Autocomplete)
```
GET /api/ListValues/GetPharmacyDiagnosisList
Response: list of diagnoses with ICD codes and descriptions
```
- Fetch full list, filter client-side by search term
- Display format: "ICD Code — Description" (e.g. "I10 — Essential (primary) hypertension")

### Add New Medication
```
POST /api/PharmacyDelivery/InsertMemberDelivery
Body: {
  "EnrolleeId": "21000645/0",
  "DiagnosisName": "Essential (primary) hypertension",
  "DiagnosisId": "I10",
  "ProcedureName": "AMLODIPINE TAB",
  "ProcedureId": "B0110045",
  "ProcedureQuantity": 3,
  "DosageDescription": "Two Tabs Daily",
  "Comment": "Doctor prescribed"
}
```

### Update Existing Medication (same API + EntryNo)
```
POST /api/PharmacyDelivery/InsertMemberDelivery
Body: {
  "EnrolleeId": "21000645/0",
  "DiagnosisName": "Essential (primary) hypertension",
  "DiagnosisId": "I10",
  "ProcedureName": "AMLODIPINE TAB",
  "ProcedureId": "B0110045",
  "ProcedureQuantity": 3,
  "DosageDescription": "Two Tabs Daily",
  "Comment": "Dosage increased by doctor",
  "EntryNo": 25447  // THIS MAKES IT AN UPDATE
}
```

### Delete Medication
```
POST /api/PharmacyDelivery/DeletedByMember
Body: {
  "EntryNo": 12345,
  "comment": "No longer needed"  // lowercase 'comment'
}
```

### Update Member Profile
```
POST /api/Member/UpdatePharmacyMemberInfo
Body: {
  "EnrolleeID": "21000645/0",
  "Email": "new@email.com",
  "Address": "12 New Street",
  "City": "Ikeja",
  "State": "Lagos",
  "PhoneNumber": "08125122303",
  "AlternativePhone": "09029393088"
}
```

---

## Database Schema (PostgreSQL)

### Tables (11)
1. **members** — enrollee profiles synced from Prognosis
2. **medications** — medications synced from Prognosis (key field: `pbm_drug_id` stores `EntryNo`)
3. **requests** — all change requests (auto-approved, pushed to Prognosis)
4. **request_logs** — audit trail (who, what, when, before/after)
5. **admins** — admin portal users
6. **resources** — newsletters, drug alerts, scarcity alerts
7. **otp_logs** — OTP verification records
8. **payments** — payment records (Coming Soon)
9. **notifications** — member notifications
10. **sync_logs** — Prognosis API call history
11. **health_readings** — BP, glucose, cholesterol readings with trend data

---

## Backend API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | Member login (Prognosis validation + local fallback) |
| POST | /api/auth/send-otp | Send OTP to registered phone |
| POST | /api/auth/verify-otp | Verify OTP and create session |
| POST | /api/auth/admin/login | Admin portal login |

### Member
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/member/profile | Get member profile |
| GET | /api/member/dashboard | Dashboard with stats + alerts |
| GET | /api/member/medications | List medications |
| POST | /api/member/profile/update-request | Submit profile update (auto-push to Prognosis) |
| GET | /api/member/search-medications?q= | Autocomplete drug search |
| GET | /api/member/search-diagnoses?q= | Autocomplete diagnosis search |
| POST | /api/member/medications/delete-with-reason | Delete medication + push to Prognosis |
| GET | /api/member/notifications | Get notifications |

### Requests
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/requests | Create request (auto-approved, auto-pushed to Prognosis) |
| GET | /api/requests/my | List member's requests |

### Refill
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/refill/request | Request medication refill |
| POST | /api/refill/suspend | Suspend refills |
| POST | /api/refill/resume | Resume refills |
| GET | /api/refill/intelligence | Refill analysis with alerts |

### Health Readings
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/health-readings | Log a reading |
| GET | /api/health-readings | List readings (with date filters) |
| GET | /api/health-readings/latest | Latest reading per type |
| GET | /api/health-readings/trends | Trend analysis (IMPROVING/STABLE/WORSENING) |
| GET | /api/health-readings/download | CSV export |
| DELETE | /api/health-readings/{id} | Delete a reading |

### Resources
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/resources | List published resources |
| GET | /api/resources/{id} | Get single resource |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/admin/requests | List all requests (grouped by member) |
| POST | /api/admin/requests/{id}/approve | Approve request |
| POST | /api/admin/requests/{id}/reject | Reject request |
| POST | /api/admin/requests/{id}/modify | Modify request |
| GET | /api/admin/audit-logs | View audit trail |
| GET | /api/admin/analytics | Dashboard analytics |
| POST | /api/resources/admin | Create resource |
| PUT | /api/resources/admin/{id} | Update resource |
| DELETE | /api/resources/admin/{id} | Delete resource |

### Utility
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| POST | /api/admin/run-seed | Create admin account + test data |
| POST | /api/admin/run-update-alerts | Load newsletters + drug alerts |
| POST | /api/admin/resync-member/{id:path} | Force re-sync member data |

---

## Key Business Rules

1. **Members NEVER directly modify PBM data** — all changes go through requests that auto-approve and push to Prognosis APIs
2. **Medications sync from Prognosis on every login** — clears local data and pulls fresh
3. **EntryNo** is the key identifier for medications — needed for edit (update) and delete operations
4. **Diagnosis must come from Prognosis API** — no manual entry, autocomplete only
5. **Drug names must come from Prognosis search API** — no manual entry, autocomplete only
6. **Health readings** are stored locally only — not synced to Prognosis
7. **OTP fallback** only triggers when primary phone validation fails
8. **Session timeout: 5 hours** (JWT)

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, React Router 6, Axios |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 16 |
| Auth | JWT (HS256) + OTP via Termii SMS |
| File Storage | AWS S3 (local fallback) |
| Payments | Paystack (Coming Soon) |
| Deployment | Render Cloud |

---

## Branding
- Logo: Leadway Health HMO (camel + sunset)
- Colors: Charcoal #262626, Red #C8102E, Orange #E87722
- Font: Inter (web-safe fallback for Leadway custom font)
- Style: Clean, minimal, card-based, mobile-first

---

## Environment Variables
```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
PROGNOSIS_API_BASE_URL=https://prognosis-api.leadwayhealth.com/api
PROGNOSIS_USERNAME=whatsappBot
PROGNOSIS_PASSWORD=...
SMS_API_KEY=... (Termii)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
CORS_ORIGINS=https://rxhub-member.onrender.com,https://rxhub-admin.onrender.com
```

---

## Live URLs
| Service | URL |
|---------|-----|
| Member Portal | https://rxhub-member.onrender.com |
| Admin Portal | https://rxhub-admin.onrender.com |
| Backend API | https://rxhub-backend.onrender.com |
| API Docs | https://rxhub-backend.onrender.com/docs |
| Features Doc | https://rxhub-member.onrender.com/features-doc.html |
| GitHub Repo | https://github.com/Fkomoni/Member-Verification (branch: claude/leadwayhmo-rxhub-setup-x9kZJ) |
