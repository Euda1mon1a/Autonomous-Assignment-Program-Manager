# Session 106: TAMC Color Scheme Implementation

**Date:** 2026-01-14
**Branch:** `claude/session-105`
**Commit:** `916b2fa7`

---

## Completed

1. **Created `tamc_color_scheme.py`** - Parses color reference XML
2. **Updated `xml_to_xlsx_converter.py`** - Applies fill colors to schedule cells
3. **Added 12 missing codes** to color scheme XML (IM, PedW, KAP, PedNF, LDNF, etc.)
4. **Added HUMAN_TODO** for color picker UI in rotation templates

---

## Font Colors (TODO - Next Session)

The XML now has a `<font_colors>` section with 5 groups:

| Group | Hex | Usage | Codes |
|-------|-----|-------|-------|
| `theme_dark` | `#000000` | Standard body text | W, FMIT, LEC, LV, GME, C, AT |
| `white` | `#FFFFFF` | On dark backgrounds | HOL, TNG, MM, FED |
| `black` | `#000000` | Default text | R1, R2, R3, ICU, [Names] |
| `red` | `#FF0000` | **+1 AT demand** (dedicated supervision) | PR, AT, VAS, VasC, COLPO, GER |
| `red` | `#FF0000` | HV = visibility for Lamoureux | HV |
| `light_gray` | `#E8E8E8` | Night Float text | NF, Peds NF |

### Current Implementation

Only uses white font on black/red **fill** backgrounds for contrast.

### Recommended: Map Font Colors

The `red` font group has semantic meaning: **activities requiring AT supervision**.

To implement:
1. Add `get_font_color(code)` method to `TAMCColorScheme`
2. Parse `<font_colors>` section in `_load_color_scheme()`
3. Apply font color in `_apply_cell_color()` method

**For unmapped codes:** Use current logic (white on dark fills, black otherwise).

---

## Semantic Groupings

| Group | Description | Codes |
|-------|-------------|-------|
| `clinical_work` | Counts toward physical capacity (max 6) | C, C30, C40, C60, CC, CV, PR, SM, VAS, GAC, HV |
| `inpatient` | Works weekends, special patterns | FMIT, NF, L&D |
| `leave_off` | Not working | W, LV, SLV, OP, OFF, PC |
| `protected_time` | Blocked, not available | HOL, LEC, TNG, MM, FED, RTRT, CLC, ATLS, ALS, BLS, PI, HC |
| `offsite` | Off-site rotations | TDY, ER, ICU, USU |
| `requires_at` | **Red font = +1 AT demand** (dedicated 1:1) | PR, VAS, COLPO, GER (HV = visibility for Lamoureux) |

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/services/tamc_color_scheme.py` | NEW - Color scheme parser |
| `backend/app/services/xml_to_xlsx_converter.py` | Added color support |
| `docs/scheduling/TAMC_Color_Scheme_Reference.xml` | Added missing codes |
| `docs/scheduling/TAMC_Color_Scheme_Reference.xlsx` | Visual reference (3 sheets) |
| `HUMAN_TODO.md` | Added color picker UI task |

---

## Test Results

- 52 fill color mappings loaded
- 952 colored cells, 0 uncolored in test xlsx
- All ROSETTA codes have color mappings

---

## Font Colors - IMPLEMENTED

### Implementation Complete

Added font color support to the color scheme:

1. **`tamc_color_scheme.py`**:
   - Added `_font_colors` dict to store code → font color mappings
   - Added parsing for `<font_colors>` section in XML
   - Added `get_font_color(code)` method and convenience function
   - Handles `theme:1` references via `actual_rgb` attribute

2. **`xml_to_xlsx_converter.py`**:
   - Updated `_apply_cell_color()` to apply font colors
   - Priority: explicit mapping > contrast fallback
   - Fallback: white text on dark backgrounds (black, red fills)

### Font Color Usage (Block10)

| Color | Count | Codes |
|-------|-------|-------|
| Red | 16 | PR, VAS, COLPO, GER, HV |
| Light Gray | 12 | NF, Peds NF |
| Black | 232 | C, W, FMIT, LV, LEC, etc. |
| Fallback (white) | 9 | Dark backgrounds without explicit mapping |

### Key Semantic Meanings

| Font Color | Meaning |
|------------|---------|
| Red (#FF0000) | **+1 AT demand** (dedicated 1:1 supervision) |
| Red (#FF0000) | HV = visibility for Lamoureux (NOT +1 AT) |
| Light Gray (#E8E8E8) | Night Float (subtle text) |
| White (#FFFFFF) | Contrast on dark backgrounds |
| Black (#000000) | Default text |

### Test Results

- 24 font color mappings loaded from XML
- 52 fill color mappings loaded from XML
- Block10 schedule: 269 cells with font colors applied
