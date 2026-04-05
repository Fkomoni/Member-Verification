# Leadway Assurance – Design Style Guide

Reference: leadway.com

---

## COLOR PALETTE

### Primary Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Leadway Orange** | `#F58220` | Primary CTA buttons, accent text, brand highlight |
| **Dark Teal** | `#2C3E4A` | Hero sections, dark backgrounds, nav bar top strip |
| **Near Black** | `#1A1A2E` | Headings, primary body text |
| **White** | `#FFFFFF` | Backgrounds, nav bar, card backgrounds |

### Secondary / Supporting Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Soft Pink / Blush** | `#FFF5F0` | Form section backgrounds, light content areas |
| **Red (asterisk)** | `#E53935` | Required field indicators (*) |
| **Light Gray** | `#E0E0E0` | Input field borders, dividers |
| **Medium Gray** | `#9E9E9E` | Placeholder text, secondary text |
| **Orange (hover)** | `#E07518` | Button hover states |

---

## TYPOGRAPHY

### Font Family
- **Primary:** Sans-serif (appears to be **Poppins** or similar geometric sans-serif)
- **Fallback:** `'Poppins', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif`

### Font Weights
| Weight | Usage |
|--------|-------|
| **700 (Bold)** | Page headings, hero text, CTA buttons |
| **600 (Semi-Bold)** | Form labels, section headers, nav links |
| **400 (Regular)** | Body text, descriptions, placeholder text |

### Font Sizes (approximate)
| Element | Size | Style |
|---------|------|-------|
| Hero heading | 48-56px | Bold, dark or white on dark bg |
| Page heading | 36-42px | Bold, italic (e.g. "Kindly fill in your personal information") |
| Section subtitle | 14-16px | Uppercase, letter-spacing 2px, semi-bold |
| Form labels | 14-16px | Semi-bold, dark text with orange/red asterisk |
| Body text | 16-18px | Regular weight, dark gray |
| Nav links | 14px | Uppercase, semi-bold, letter-spacing 1-2px |
| Button text | 16-18px | Bold, white on orange |

---

## FORM DESIGN

### Input Fields
- **Background:** White (`#FFFFFF`)
- **Border:** 1px solid light gray (`#E0E0E0`)
- **Border Radius:** 8-10px (rounded corners)
- **Padding:** 16px horizontal, 14px vertical
- **Placeholder color:** Medium gray (`#9E9E9E`)
- **Font size:** 16px

### Form Layout
- **Two-column grid** on desktop (side by side fields)
- **Single column** on mobile
- **Gap between fields:** ~24px vertical, ~24px horizontal
- **Form container background:** Soft pink/blush (`#FFF5F0`)
- **Form container padding:** 40-60px

### Labels
- **Position:** Above the input field
- **Color:** Dark near-black (`#1A1A2E`)
- **Required indicator:** Red asterisk (`*`) in `#E53935`
- **Margin bottom:** 8px from input

### Select Dropdowns
- Same styling as text inputs
- Chevron icon on the right side

### Textarea
- Same border/radius as inputs
- Taller height for address fields

---

## BUTTONS

### Primary CTA (Continue to Payment)
- **Background:** Leadway Orange (`#F58220`)
- **Text:** White, bold, 16-18px
- **Border Radius:** 8-10px
- **Padding:** 16px 32px
- **Full width** in form context (spans column)
- **Arrow icon** on the right side (`->`)
- **Hover:** Slightly darker orange (`#E07518`)

### Secondary / Back Button
- **Background:** White / transparent
- **Border:** 1px solid light gray
- **Text:** Dark, bold
- **Arrow icon** on the left side (`<-`)
- **Border Radius:** 8-10px

### Outline Button (Compare Plans)
- **Background:** Transparent
- **Border:** 2px solid Leadway Orange
- **Text:** Leadway Orange, bold
- **Border Radius:** 25px (pill shape)

### Chat FAB (Floating Action Button)
- **Background:** Leadway Orange (`#F58220`)
- **Shape:** Rounded pill
- **Text:** White "Chat with us"
- **Icon:** Chat bubble icon
- **Position:** Fixed bottom-right

---

## NAVIGATION

### Top Bar
- **Background:** White
- **Height:** ~80px
- **Logo:** Left-aligned (Leadway camel logo with sunset)
- **Nav links:** Center/right, uppercase, semi-bold, 14px
- **Letter spacing:** 1-2px on nav items
- **Hamburger menu:** Right side on mobile (3 horizontal lines)
- **Top accent strip:** Thin dark teal/gradient bar at very top of page

### Breadcrumbs
- **Style:** `Home / Householder`
- **Color:** Medium gray
- **Separator:** `/`

---

## HERO SECTIONS

### Dark Hero (Product Selection)
- **Background:** Dark teal (`#2C3E4A`)
- **Heading:** White, large (48-56px), bold
- **Subtitle/label:** Uppercase, letter-spacing, smaller, white/light
- **Sub-instruction:** Uppercase, muted white, smaller

### Light Hero (Landing Pages)
- **Background:** White
- **Category label:** Uppercase, small, orange or dark
- **Heading:** Very large (56px+), bold, dark
- **Description:** Regular weight, medium gray, 18px

---

## SPACING & LAYOUT

### Container
- **Max width:** ~1200px
- **Padding:** 0 60px (desktop), 0 20px (mobile)
- **Centered** horizontally

### Section Spacing
- **Between sections:** 60-80px
- **Form section padding:** 40-60px all sides
- **Between form rows:** 24px

### Border Radius
- **Cards/Containers:** 12-16px
- **Inputs/Buttons:** 8-10px
- **Pill buttons:** 25px

---

## COMPONENT PATTERNS

### Consent Checkbox
- Standard checkbox
- Text: Regular weight, 14-16px, dark gray
- Links (e.g., "Privacy Policy") in orange

### Links
- **Color:** Leadway Orange (`#F58220`)
- **Style:** No underline by default, underline on hover

---

## CSS VARIABLES (Ready to Use)

```css
:root {
  /* Colors */
  --leadway-orange: #F58220;
  --leadway-orange-hover: #E07518;
  --leadway-dark-teal: #2C3E4A;
  --leadway-near-black: #1A1A2E;
  --leadway-white: #FFFFFF;
  --leadway-blush: #FFF5F0;
  --leadway-red: #E53935;
  --leadway-gray-light: #E0E0E0;
  --leadway-gray-medium: #9E9E9E;
  --leadway-gray-dark: #616161;

  /* Typography */
  --font-family: 'Poppins', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  --font-weight-regular: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Spacing */
  --container-max-width: 1200px;
  --section-padding: 60px;
  --form-gap: 24px;
  --input-padding: 16px;

  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-pill: 25px;
}
```

---

## USAGE NOTES

- Always use the blush/soft pink background for form sections
- Orange is reserved for primary actions only — do not overuse
- Dark teal for hero/header sections that need contrast
- Keep forms in a two-column grid on desktop
- Uppercase + letter-spacing for category labels and nav items
- All required fields must show the red asterisk
