# LeadwayHMO RxHub — Design Brief for Claude Design

## Project Overview
Design a **PBM (Pharmacy Benefit Management) Member Self-Service Web App** for Leadway Health HMO. This is a super app where enrollees manage their entire medication lifecycle — viewing prescriptions, editing dosages, adding/deleting medications, tracking health readings, and accessing health resources.

---

## Brand Identity

### Logo
- Leadway Health HMO logo: Camel silhouette inside sunset circle + "LEADWAY Health HMO" text
- Logo file: https://raw.githubusercontent.com/Fkomoni/datadump/main/leadway%20health%20logo%2020266.jpg

### Colors (from De Novo Style Guide)
| Color | Hex | Usage |
|-------|-----|-------|
| Charcoal | #262626 | Sidebar, dark backgrounds, primary text |
| Crimson Red | #C8102E | Primary buttons, accents, alerts, logo text |
| Orange | #E87722 | Secondary buttons, warnings, category tags |
| Yellow/Gold | #F7B424 | Highlights, from logo gradient |
| Light Grey | #F5F5F7 | Page backgrounds |
| White | #FFFFFF | Cards, inputs |
| Green | #16A34A | Success, active status, approved badges |
| Blue | #2563EB | Info, edit actions |
| Purple | #7C3AED | Modified status |

### Typography
- Primary: Inter (web-safe fallback for Leadway custom font)
- Headlines: Inter Bold/700
- Body: Inter Regular/400
- Small: Inter Medium/500

---

## App Structure (Pages)

### 1. LOGIN PAGE
- Leadway Health logo (large, centered)
- "RxHub" title in red
- "Member Self-Service Portal" subtitle
- Member ID input (placeholder: "e.g. 23069157/0")
- Phone Number input (placeholder: "e.g. 08012345678")
- "Sign In" button (red)
- OTP fallback screen (shown when primary login fails)
- Dark charcoal (#262626) background

### 2. SIDEBAR (persistent, left side)
- Leadway logo at top
- "RxHub" in red, "Member Self-Service" subtitle
- Navigation links:
  - Dashboard
  - Medications
  - Health Readings
  - My Requests
  - New Request
  - Resources
  - Profile
- Member name + ID at bottom
- Sign Out button
- Active link: highlighted with white bg opacity

### 3. DASHBOARD
- Welcome message: "Welcome back, {FirstName}"
- Subtext: ID, Scheme name, Diagnosis
- 3 stat cards: Medications count, Pending Requests, Unread Alerts
- Upcoming Refills section: cards with drug name, next refill date, days-left badge (color-coded: red=overdue, orange=soon, blue=ok)
- Quick Actions: 3 buttons — View Medications, New Request, Log Health Reading

### 4. MEDICATIONS PAGE
- Header: "My Medications" + "Add Medication" button (red outline) + "Request All Refills" button (dark)
- Grid of medication cards, each showing:
  - Drug name (bold, large)
  - Generic name (grey, smaller)
  - Status badge (ACTIVE = green)
  - 4 detail fields: Dosage, Frequency, Days Supply, Refills Used
  - Next Refill Date bar (blue background) with OVERDUE tag if past due
  - 3 action buttons:
    - "Request Refill" (dark, full width)
    - "Edit" (blue outline) — opens inline edit form
    - "Delete" (red outline) — prompts for reason
- **Inline Edit Form** (expands within card when Edit clicked):
  - "Edit {DrugName}" title
  - New Dosage / Directions input
  - Quantity input
  - Reason for change input
  - Save Changes (blue) + Cancel buttons

### 5. HEALTH READINGS PAGE
- Header: "Health Readings" + "+ Log Reading" button (red)
- **Entry Form** (expandable):
  - 3 type toggles: Blood Pressure / Blood Glucose / Cholesterol
  - BP: Systolic + Diastolic inputs
  - Glucose: Level + Context dropdown (Fasting/Random/Post-meal)
  - Cholesterol: Total, HDL, LDL, Triglycerides
  - Notes field
  - Save Reading button
- **3 Trend Cards** (one per type):
  - Type label (orange uppercase)
  - Trend badge: "Improving" (green arrow down), "Stable" (blue), "Worsening" (red arrow up)
  - Large value (e.g. "120/80")
  - Unit (mmHg, mg/dL)
  - Clinical classification (Normal, Elevated, High, etc.)
  - Change vs previous (e.g. "-7/-6 mmHg")
  - Date + reading count
- **History Table**:
  - Filter buttons: All / Blood Pressure / Blood Glucose / Cholesterol
  - Date range pickers (From / To)
  - "Download CSV" button
  - Table: Date & Time, Type, Reading (with trend arrow), Status (color-coded), Notes
  - Per-row trend arrows: green down = improving, red up = worsening

### 6. MY REQUESTS PAGE
- Table: Date, Type, Action, Status badge, Comment
- Status colors: Pending=orange, Approved=green, Rejected=red, Modified=purple
- Admin response section for requests with admin comments (green background)

### 7. NEW REQUEST PAGE
- 2 tabs: "Profile Update" / "Medication Change"
- **Profile Update tab**:
  - Phone, Alternative Phone, Email, Address, City, State inputs
  - Reason field
  - Submit button
- **Medication Change tab**:
  - 3 action toggles: Add New / Remove / Modify
  - **Medication Search** (autocomplete):
    - Red-bordered input
    - Dropdown showing drug names + IDs from Prognosis database
    - Green "Selected" confirmation bar
  - Quantity input
  - Dosage / Directions input
  - **Diagnosis Search** (autocomplete):
    - Input that searches ICD codes
    - Dropdown showing "ICD Code — Description"
    - Green "Selected" confirmation bar
  - Comment / Reason textarea
  - Prescription Upload (file input, for Add only)
  - Submit button (red)

### 8. RESOURCES PAGE
- Filter buttons: All, Newsletter, Health Tip, Drug Alert, Scarcity Alert, PBM Update
- Color-coded category badges per card
- Card grid:
  - Category tag (colored)
  - Title (bold)
  - Body text (expandable for long alerts — "Read full alert" button)
  - Diagnosis tags
  - Date
  - "Read Full Newsletter →" link for newsletter cards (opens full HTML in new tab)

### 9. PROFILE PAGE
- Avatar circle with initials
- Name (large)
- Member ID
- Read-only fields: Email, Phone, DOB, Gender, Diagnosis, Plan, Employer, Status
- Note: "To update, go to New Request > Profile Update"
- Sign Out button (red outline)

---

## Design Guidelines
- Mobile-responsive (works on phones + desktop)
- Card-based UI with subtle shadows
- Clean, minimal, strong spacing
- No unnecessary decoration
- Accessible (good contrast, clear labels)
- All buttons have hover states
- Dropdowns should be clean with clear separation between items
- Forms should have clear labels above inputs
- Status badges should be pill-shaped with appropriate colors
- Tables should have alternating row backgrounds on hover

---

## Design Deliverables
1. Full page designs for all 9 pages listed above
2. Component library (buttons, inputs, cards, badges, dropdowns)
3. Login flow (primary + OTP fallback)
4. Medication edit inline flow
5. Health readings entry + trend cards
6. Autocomplete dropdown component (for meds + diagnosis search)
7. Mobile responsive versions
