# Leadway Householder Pricing Engine — Product Document

**Version:** 2.0
**Date:** April 2026
**Built by:** Leadway Digital Engineering
**Platform:** Web Application (FastAPI + HTML/CSS/JS)
**Live URL:** https://leadway-pricing-engine.onrender.com

---

## 1. EXECUTIVE SUMMARY

The Leadway Householder Pricing Engine is a web-based tool that generates instant premium quotes for Householder Insurance policies. It uses Leadway Assurance's official rate tables to calculate premiums across 6 coverage sections, with separate pricing for **Individual (Retail)** and **Corporate (Commercial)** segments.

The engine replaces manual spreadsheet-based quoting — reducing quote turnaround from **up to 1 hour to under 60 seconds**.

---

## 2. BUSINESS CONTEXT

### Problem
- Householder premium quotes were generated manually by underwriters using spreadsheets
- Quoting took up to 1 hour per policy
- No standardized pricing — rates varied by underwriter
- No visibility into portfolio performance or pricing consistency

### Solution
- Automated pricing engine using official Leadway rate tables
- Instant quote generation via web interface
- Consistent pricing across all branches and underwriters
- Separate logic for Individual (pre-priced) and Corporate (underwritten) segments

### Data Foundation
- **8,906 production records** (2022–2025)
- **342 claims** totaling N219M
- **N845M+ premium portfolio**
- **1,410 active policies**
- Overall loss ratio: 34.6%
  - Corporate: 13.4%
  - Individual: 31.5%

---

## 3. PRODUCT FEATURES

### 3.1 Landing Page
- Single "Get a Quote" card with hero image
- Policy Documents section (summary modal + downloadable PDF)
- "Our Products" dropdown navigation (Householder active; Motor and Fire coming soon)
- Stats bar showing portfolio metrics

### 3.2 Quote Builder (3-Step Form)
- **Step 1 — Property Information**
  - Property address
  - Location / State (Lagos, Abuja, Port Harcourt, Ibadan, Kaduna, Other)
  - Building age
  - Building sum insured (NGN)
  - Content sum insured (NGN)

- **Step 2 — Coverage Selection**
  - Core coverages with image cards:
    - Building (Fire & Special Perils)
    - Content (Fire, Burglary & Special Perils)
  - Additional coverages:
    - Accidental Damage to content
    - All Risks Extension (max 10% of content SI)
    - Personal Accident
    - Alternative Accommodation

- **Step 3 — Policy Details**
  - Cover type selection with descriptions (Basic → Platinum)
  - Policy duration (3–12 months)
  - Claims history (last 3 years)
  - Risk mitigation discounts:
    - Security system installed (-5%)
    - Fire extinguisher on premises (-3%)

### 3.3 Corporate / Individual Toggle
- Switches between pre-priced (Individual) and underwritten (Corporate) rates
- Building coverage image changes based on selection
- Left info panel updates with segment-specific messaging

### 3.4 Results Page (Split Layout)
- Left panel: Gross premium, rate per mille, per-section breakdown
- Right panel: Summary card, adjustments table, net premium, commission
- Print-friendly output
- "Modify Quote" and "New Quote" actions

### 3.5 Rate Card Modal
- Styled overlay showing official Individual and Corporate rates
- Accessible from top navigation

### 3.6 Policy Documents
- "View Policy Summary" — formatted modal with all 5 sections, 13 insured perils, limits of liability, and key conditions
- "Download Full Policy" — official 15-page PDF (Houseowners & Householders Insurance Policy)

### 3.7 API Endpoints
- `POST /api/quote` — Generate a premium quote
- `GET /api/rates` — Return the current rate card
- `GET /docs` — Interactive API documentation (Swagger UI)

---

## 4. PRICING LOGIC

### 4.1 Rate Tables (from official PRICING.xlsx)

**Individual (Pre-Priced — Fixed Rates)**

| Coverage | Rate | Applied To |
|----------|------|------------|
| Building (Fire & Special Perils) | 0.10% | Building SI |
| Content (Fire, Burglary & Special Perils) | 0.20% | Content SI |
| Accidental Damage | 0.125% | Content SI |
| All Risks Extension | 2.0% | 10% of Content SI |
| Personal Accident | 0.185% | Total SI |
| Alternative Accommodation | 0.20% | Building SI |

**Corporate (Underwritten — 4 Rate Bands)**

| Coverage | Band 1 (Basic/Bronze) | Band 2 (Silver/Standard) | Band 3 (Gold) | Band 4 (Platinum) |
|----------|------|------|------|------|
| Building | 0.125% | 0.15% | 0.175% | 0.185% |
| Content | 0.30% | 0.35% | 0.45% | 0.50% |

### 4.2 Cover Types

| Tier | Description | Target |
|------|-------------|--------|
| **Basic** | Building only — fire & special perils | Budget-conscious |
| **Bronze** | Building + contents with basic burglary | Entry-level |
| **Silver** | Building + contents + accidental damage | Mid-range |
| **Standard** | Full building + contents + burglary + special perils | Most popular |
| **Gold** | Standard + all risks + personal accident | Enhanced |
| **Platinum** | Comprehensive — all coverages + alt. accommodation | Premium |

### 4.3 Adjustments

| Factor | Logic |
|--------|-------|
| **Location** | Lagos +15%, Port Harcourt +10%, Abuja +5%, Ibadan -5%, Kaduna -10% |
| **Cover type** (Individual only) | Basic 0.85x → Platinum 1.20x |
| **Building age** | 0-5yr: 0%, 6-15yr: +5%, 16-30yr: +10%, 30+yr: +20% |
| **Claims history** | 0 claims: 0%, 1: +10%, 2: +25%, 3: +50%, 4+: +75% |
| **Security system** | -5% discount |
| **Fire extinguisher** | -3% discount |
| **Volume discount** (Corporate) | 100M+: -4%, 500M+: -7%, 1B+: -10% |
| **Short period** | Pro-rata with 15% loading for <12 months |

### 4.4 Minimum Premiums
- Corporate: N25,000
- Individual: N5,000

### 4.5 Commission
- 15% of gross premium (both segments)

### 4.6 Calculation Flow

```
1. Apply base rate × sum insured (per section)
2. Sum all section premiums → Base Premium
3. Apply location factor
4. Apply cover type multiplier (Individual only)
5. Apply building age loading
6. Apply claims history loading
7. Subtract security discount
8. Subtract fire equipment discount
9. Apply volume discount (Corporate)
10. Apply duration adjustment (short period)
11. Apply minimum premium floor
12. Calculate commission (15%)
13. Net Premium = Gross - Commission
```

---

## 5. TECHNICAL ARCHITECTURE

### 5.1 Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Icons | Lucide Icons |
| Font | Montserrat (Google Fonts) |
| Deployment | Render (Web Service) |
| Repository | GitHub (Fkomoni/Member-Verification) |

### 5.2 File Structure

```
pricing-engine/
├── api/
│   └── main.py              # FastAPI app, routes, CORS
├── engine/
│   ├── __init__.py           # Package exports
│   ├── models.py             # Data models (RiskProfile, PremiumBreakdown)
│   ├── rates.py              # Official rate tables, location factors, discounts
│   └── calculator.py         # Premium calculation logic
├── frontend/
│   ├── index.html            # Multi-page SPA (Select → Quote → Results)
│   ├── styles.css            # Full CSS (Leadway brand guide compliant)
│   ├── app.js                # Page navigation, form logic, API calls
│   ├── leadway-logo.jpeg     # Leadway Assurance logo
│   └── Leadway-Householder-Policy.pdf  # Official policy document
└── requirements.txt          # Python dependencies
```

### 5.3 API Reference

**POST /api/quote**

Request:
```json
{
  "client_type": "individual",
  "building_sum_insured": 50000000,
  "content_sum_insured": 10000000,
  "location": "lagos",
  "cover_type": "standard",
  "include_building": true,
  "include_content": true,
  "include_accidental_damage": false,
  "include_all_risks": false,
  "include_personal_accident": false,
  "include_alt_accommodation": false,
  "building_age_years": 0,
  "has_security": false,
  "has_fire_extinguisher": false,
  "claims_history_count": 0,
  "policy_duration_months": 12
}
```

Response:
```json
{
  "building_premium": 50000.0,
  "content_premium": 20000.0,
  "accidental_damage_premium": 0.0,
  "all_risks_premium": 0.0,
  "personal_accident_premium": 0.0,
  "alt_accommodation_premium": 0.0,
  "base_premium": 70000.0,
  "location_adjustment": 10500.0,
  "cover_type_adjustment": 0.0,
  "claims_loading": 0.0,
  "security_discount": 0.0,
  "fire_equipment_discount": 0.0,
  "duration_adjustment": 0.0,
  "gross_premium": 78085.0,
  "commission": 11712.75,
  "net_premium": 66372.25,
  "rate_per_mille": 1.3014,
  "client_type": "individual",
  "coverages": ["Building (Fire & Special Perils)", "Content (Fire, Burglary & Special Perils)"]
}
```

---

## 6. BRAND COMPLIANCE

The application follows the official Leadway Assurance Brand Guidelines:

| Attribute | Implementation |
|-----------|---------------|
| Primary Orange | `#FF6B22` (RGB 255, 107, 34) |
| Primary Dark | `#333333` (RGB 51, 51, 51) |
| White | `#FFFFFF` |
| Color Ratio | 60% orange / 20% dark / 20% white |
| Typography | Montserrat — bold, geometric sans-serif |
| Headlines | Uppercase, 900 weight |
| Photography | Black people only; warm, natural lighting; authentic and candid |
| Visual Direction | Sophisticated, minimal, generous spacing, intentional use of color |
| Logo | Official Leadway Assurance logo (camel mark) |

---

## 7. POLICY COVERAGE SUMMARY

Based on the official Houseowners & Householders Insurance Policy:

### Sections
1. **Section I** — Loss or Damage to the Buildings
2. **Section II** — Loss or Damage to the Contents
3. **Section III** — Alternative Accommodation & Loss of Rent
4. **Section IV** — Liability to the Public
5. **Section V** — Compensation for Death of the Insured

### Insured Perils
Fire, Lightning, Explosion, Theft (forcible entry), Riot & Strike, Malicious Damage, Aircraft Impact, Burst Pipes, Impact Damage, Earthquake/Volcanic Eruption, Hurricane/Cyclone/Tornado/Windstorm, Flood, Storm

### Limits of Liability
- Section I: Sum Insured on each item
- Section II: 3% per article (Jewellery exclusive); Platinum items at 10% of Contents SI or N500,000
- Section III: 10% of Building SI + 10% of Contents SI
- Section IV: N250,000 per event
- Section V: N25,000 or half of Total Sum (whichever is less)

---

## 8. DEPLOYMENT

### Current Deployment
- **Platform:** Render
- **Service:** leadway-pricing-engine
- **Branch:** claude/update-skill-Wjh28
- **Auto-deploy:** On push to branch
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### Environment
- Python 3.11.9
- No database required (stateless pricing logic)
- No environment variables required

---

## 9. FUTURE ROADMAP

### Phase 2 — Enhancements
- [ ] User authentication for brokers/agents
- [ ] Quote history and PDF generation
- [ ] Email quote to client
- [ ] Integration with Leadway core insurance system
- [ ] Admin panel for rate table management

### Phase 3 — New Products
- [ ] Motor Insurance pricing engine
- [ ] Fire Insurance pricing engine
- [ ] Marine Insurance pricing engine

### Phase 4 — Intelligence
- [ ] Claims prediction model
- [ ] Dynamic pricing based on claims experience
- [ ] Portfolio analytics dashboard
- [ ] Loss ratio monitoring by segment

---

## 10. DATA SOURCES

| Source | Description | Records |
|--------|-------------|---------|
| Householder Report.xlsx | Production & claims data (2022–2025) | 8,906 policies, 342 claims |
| PRICING.xlsx | Official rate tables (pre-priced + underwritten) | 6 coverage types, 4 bands |
| Householder Policy Draft (PDF) | Official policy wording (15 pages) | 5 sections, 13 perils |
| Leadway Brand Guidelines | Colors, typography, photography, visual direction | Full brand system |

---

*Document generated April 2026. Leadway Assurance Company Limited (RC 7588).*
