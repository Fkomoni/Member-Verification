# Biometric Member Verification Portal — Architecture

## System Overview

A biometric verification platform for health insurance providers to authenticate
member identity at point-of-care using fingerprint scanning, integrated with the
**Prognosis** core HMO system.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PROVIDER WORKSTATION                         │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────────┐   ┌───────────────┐  │
│  │  Fingerprint  │◄──►│  Fingerprint Bridge  │◄──►│  React Portal │  │
│  │  Scanner HW   │    │  (vendor WebSocket)  │   │  (Frontend)   │  │
│  └──────────────┘    └──────────────────────┘   └───────┬───────┘  │
│                                                         │ HTTPS    │
└─────────────────────────────────────────────────────────┼──────────┘
                                                          │
                    ┌─────────────────────────────────────▼──────────┐
                    │               BACKEND (FastAPI)                │
                    │                                                │
                    │  /api/v1/login                                 │
                    │  /api/v1/verify-member                         │
                    │  /api/v1/capture-biometric                     │
                    │  /api/v1/validate-fingerprint                  │
                    │  /api/v1/log-visit                             │
                    │  /api/v1/validate-claim                        │
                    │                                                │
                    │  ┌────────────┐  ┌───────────────────────┐    │
                    │  │ JWT Auth   │  │ Biometric Service      │    │
                    │  │ Middleware │  │ (encrypt/decrypt/match)│    │
                    │  └────────────┘  └───────────────────────┘    │
                    │                                                │
                    └──────────┬──────────────────┬─────────────────┘
                               │                  │
                    ┌──────────▼──────┐  ┌────────▼──────────────┐
                    │  PostgreSQL DB  │  │  Prognosis Core API   │
                    │                 │  │  (HMO System)         │
                    │  - members      │  │                       │
                    │  - biometrics   │  │  - Member lookup      │
                    │  - providers    │  │  - Claim verification │
                    │  - visits       │  │  - Fraud flagging     │
                    │  - verif. logs  │  │                       │
                    └─────────────────┘  └───────────────────────┘
```

## Member Check-In Flow

```
Provider logs in
       │
       ▼
 Input Enrollee ID ──► POST /verify-member
       │
       ▼
┌──────────────────────┐
│ Has biometric on file?│
└──────┬───────┬───────┘
       │       │
      NO      YES
       │       │
       ▼       ▼
  Capture    Scan fingerprint
  fingerprint  POST /validate-fingerprint
  POST /capture-biometric
       │       │
       ▼       ├──► MATCH ──► Approved ──► Generate token
  Enrolled     │              Log visit
               └──► NO MATCH ──► Denied
                               Flag impersonation
                               Refer to HMO
```

## Claims Validation Rule

Every claim submitted to the HMO must include:
- **Verification token** (JWT signed by this system)
- **Timestamp** of the visit
- **Provider ID**

`POST /validate-claim` checks these against the visits table.
If no valid approved visit exists → **claim is rejected**.

## Database Schema

| Table              | Purpose                                      |
|--------------------|----------------------------------------------|
| `members`          | Enrollee demographic data + biometric flag   |
| `biometrics`       | AES-encrypted fingerprint templates          |
| `providers`        | Healthcare provider accounts                 |
| `visits`           | Verified check-in records + tokens           |
| `verification_logs`| Full audit trail of every scan attempt       |

See `database/schema.sql` for the full DDL.

## Security

| Concern                | Solution                                          |
|------------------------|---------------------------------------------------|
| Fingerprint storage    | Fernet (AES-128-CBC) encrypted templates, NOT raw images |
| Authentication         | JWT with expiring tokens (HS256)                  |
| Password storage       | bcrypt hashing via passlib                        |
| Audit trail            | Every verification attempt logged with timestamp  |
| Fraud detection        | Mismatches flagged to Prognosis for HMO review    |
| Transport              | HTTPS enforced in production                      |
| CORS                   | Restricted to portal origin                       |

## Tech Stack

| Layer      | Technology        |
|------------|-------------------|
| Frontend   | React 18          |
| Backend    | FastAPI (Python)  |
| Database   | PostgreSQL        |
| Auth       | JWT (python-jose) |
| Encryption | cryptography (Fernet) |
| Biometric  | Vendor SDK via WebSocket bridge |

## Prognosis Integration

The `prognosis_client.py` service module handles all outbound calls:

- **`lookup_member(enrollee_id)`** – Sync member data from Prognosis
- **`submit_claim_verification(...)`** – Notify Prognosis of verified visits
- **`flag_impersonation(member_id, provider_id)`** – Report biometric mismatches

Configure via `PROGNOSIS_BASE_URL` and `PROGNOSIS_API_KEY` env vars.

## Fingerprint Device Integration

The frontend `fingerprintBridge.js` module abstracts scanner hardware:

1. **WebSocket SDK** (recommended) — vendor agent runs on PC, browser connects via `ws://localhost:<port>`
2. **Browser Plugin** — legacy ActiveX/NPAPI approach
3. **Electron bridge** — call native SDK via Node.js

Replace the demo stub in `fingerprintBridge.js` with your vendor's API.
Supported vendors: SecuGen, DigitalPersona, Futronic, Suprema, ZKTeco.

## Running Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with real values
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```
