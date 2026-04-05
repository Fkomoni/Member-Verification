# REBUILD PROMPT — Leadway Householder Pricing Engine

> Copy and paste this entire prompt into Claude Code to rebuild the pricing engine from scratch.

---

## CONTEXT

I need to build a **Householder Insurance Pricing Engine** for **Leadway Assurance**, a major Nigerian insurance company. The engine generates instant premium quotes for householder policies using official Leadway rate tables.

## BRAND GUIDELINES

Follow these EXACTLY:
- **Primary Orange**: `#FF6B22` (RGB 255, 107, 34) — use for 60% of the design
- **Primary Dark**: `#333333` (RGB 51, 51, 51) — use for 20%
- **White**: `#FFFFFF` — use for 20%
- **Font**: Montserrat (Google Fonts) — geometric, bold, structured
- **Headlines**: UPPERCASE, 900 weight (Black)
- **Sub-heads**: 800 weight, uppercase
- **Body text**: 500 weight, clean
- **Photography**: Only show Black people. Warm, natural lighting. Authentic and candid.
- **Visual direction**: Sophisticated, minimal, generous spacing. Confident and calm, never cluttered.
- **Logo**: I will provide my Leadway Assurance logo (camel mark). Use it in navbar, quote builder panel, results panel, and footer.

## RATE TABLES (Official)

### Individual / Retail (Pre-Priced — Fixed Rates)

| Coverage | Rate | Applied To |
|----------|------|------------|
| Building (Fire & Special Perils) | 0.10% (0.001) | Building Sum Insured |
| Content (Fire, Burglary & Special Perils) | 0.20% (0.002) | Content Sum Insured |
| Accidental Damage to content | 0.125% (0.00125) | Content Sum Insured |
| All Risks Extension | 2.0% (0.02) | 10% of Content Sum Insured |
| Personal Accident | 0.185% (0.00185) | Total Sum Insured |
| Alternative Accommodation | 0.20% (0.002) | Building Sum Insured |

### Corporate / Commercial (Underwritten — 4 Rate Bands)

| Coverage | Band 1 | Band 2 | Band 3 | Band 4 |
|----------|--------|--------|--------|--------|
| Building | 0.125% | 0.15% | 0.175% | 0.185% |
| Content | 0.30% | 0.35% | 0.45% | 0.50% |

Band mapping to cover types: Basic/Bronze → Band 1, Silver/Standard → Band 2, Gold → Band 3, Platinum → Band 4.

Corporate uses same rates as Individual for additional coverages (Accidental Damage, All Risks, PA, Alt Accommodation).

## COVER TYPES

| Tier | Description |
|------|-------------|
| Basic | Building only — fire & special perils |
| Bronze | Building + contents with basic burglary |
| Silver | Building + contents + accidental damage |
| Standard | Full building + contents + burglary + special perils (MOST POPULAR) |
| Gold | Standard + all risks extension + personal accident |
| Platinum | Comprehensive — all coverages + alternative accommodation |

## ADJUSTMENTS & LOADINGS

- **Location factors**: Lagos +15%, Port Harcourt +10%, Abuja +5%, Ibadan -5%, Kaduna -10%, Other 0%
- **Building age**: 0-5yr: 0%, 6-15yr: +5%, 16-30yr: +10%, 30+yr: +20%
- **Claims history**: 0 claims: 0%, 1: +10%, 2: +25%, 3: +50%, 4+: +75% (cap)
- **Security system discount**: -5%
- **Fire extinguisher discount**: -3%
- **Volume discount** (Corporate): 100M+ SI: -4%, 500M+ SI: -7%, 1B+ SI: -10%
- **Volume discount** (Individual): 50M+ SI: -3%, 100M+ SI: -5%
- **Short period loading**: Pro-rata with 15% loading for policies under 12 months
- **Minimum premium**: Corporate N25,000, Individual N5,000
- **Commission**: 15% of gross premium (both segments)

## CALCULATION FLOW

```
1. Apply base rate × sum insured for each selected coverage section
2. Sum all section premiums → Base Premium
3. Apply location factor to base
4. Apply cover type multiplier (Individual only — Corporate uses rate bands)
5. Apply building age loading
6. Apply claims history loading
7. Subtract security discount
8. Subtract fire equipment discount
9. Apply volume discount
10. Apply duration adjustment (pro-rata + 15% short period loading)
11. Apply minimum premium floor
12. Calculate commission at 15%
13. Net Premium = Gross Premium - Commission
```

## WHAT TO BUILD

### Tech Stack
- **Backend**: Python + FastAPI
- **Frontend**: Single HTML file with CSS and JS (no framework)
- **Icons**: Lucide Icons (CDN)
- **Deployment**: Render (render.yaml included)

### Structure
```
pricing-engine/
├── api/main.py               # FastAPI app with /api/quote and /api/rates
├── engine/
│   ├── __init__.py
│   ├── models.py             # RiskProfile, PremiumBreakdown dataclasses
│   ├── rates.py              # Rate tables, location factors, discounts
│   └── calculator.py         # Premium calculation logic
├── frontend/
│   ├── index.html            # Multi-page SPA
│   ├── styles.css            # Brand-compliant CSS
│   ├── app.js                # Navigation, form logic, API calls
│   └── leadway-logo.jpeg     # Logo file (I will provide)
├── requirements.txt          # fastapi, uvicorn, pydantic
└── render.yaml               # Render deployment config
```

### Frontend Flow (3 Pages in Single HTML)

**Page 1 — Landing / Product Selection**
- Orange hero section with headline "PROTECT YOUR PROPERTY. GET COVERED TODAY."
- Single large "Get a Quote" card with property image, description, coverage tags, and orange CTA button
- Policy Documents section: "View Policy Summary" (modal) + "Download Full Policy" (PDF)
- "Our Products" dropdown in nav (Householder active; Motor & Fire as "Coming Soon")
- Stats bar with dark background showing portfolio metrics
- Rate Card link opens a styled modal overlay (not raw JSON)

**Page 2 — Quote Builder (CoverageX-style split layout)**
- LEFT: Dark (#333) info panel with orange accents — logo, product description, feature checkmarks with orange left borders, "What Happens Next" steps with orange number circles
- RIGHT: White form panel with:
  - Corporate / Individual toggle (orange pill when active)
  - Step 1: Property Information (address, location, building age, building SI, content SI)
  - Step 2: Coverage Selection — image cards for each coverage type with photo thumbnails, checkmarks, rate badges. Core: Building + Content. Additional: Accidental Damage, All Risks, Personal Accident, Alt Accommodation
  - Step 3: Policy Details — cover type selector with description cards (radio buttons showing what each tier includes), duration, claims history, security/fire equipment toggle switches
  - Orange CTA button: "GET YOUR HOUSEHOLDER QUOTE"

**Page 3 — Results (Split layout)**
- LEFT: Dark (#333) panel with orange premium amount, rate per mille, per-section mini cards
- RIGHT: White panel with badges, summary card, adjustments breakdown table, net premium card (dark bg with orange total), print/new quote buttons

### API
- `POST /api/quote` — accepts RiskProfile, returns PremiumBreakdown
- `GET /api/rates` — returns rate card JSON
- `GET /docs` — Swagger UI (link in footer only, not nav)
- `GET /` — serves the frontend

### Key Details
- Building coverage image should swap: residential home for Individual, office building for Corporate
- Cover type rates in the coverage cards should update dynamically when switching Individual/Corporate
- Form backgrounds: white with light gray borders (clean, not heavy)
- All images from Unsplash — no white/blurred photos, no non-Black people in any human photos
- Policy summary modal shows: 5 sections of cover, 13 insured perils as tags, limits of liability table, key conditions, download button
- Rate card modal shows: Individual rates table + Corporate rates table with all 4 bands
- Footer: dark #333, 4 columns (brand+logo, products, developer links, company), API docs link here
- Print stylesheet hides nav/footer, shows results only
- Mobile responsive

### Render Deployment (render.yaml)
```yaml
services:
  - type: web
    name: leadway-pricing-engine
    runtime: python
    region: oregon
    rootDir: pricing-engine
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.9"
```

## POLICY DOCUMENT

The Householder Policy covers 5 sections:
1. Section I — Loss/Damage to Buildings
2. Section II — Loss/Damage to Contents
3. Section III — Alternative Accommodation & Loss of Rent
4. Section IV — Liability to the Public
5. Section V — Compensation for Death of Insured

Insured Perils: Fire, Lightning, Explosion, Theft (forcible entry), Riot & Strike, Malicious Damage, Aircraft Impact, Burst Pipes, Impact Damage, Earthquake/Volcano, Hurricane/Cyclone, Flood, Storm

Limits: Section I = SI per item, Section II = 3% per article, Section III = 10% Bldg SI + 10% Content SI, Section IV = N250,000/event, Section V = N25,000 or half total sum.

Include the policy summary as a viewable modal on the landing page.

## BUILD IT

Build the entire system — engine, API, frontend, deployment config. Make it production-ready, brand-compliant, and deployable to Render. Use the exact rate tables and calculation logic specified above. The frontend should look like a professional insurance website, not a developer tool.
