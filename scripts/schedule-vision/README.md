# Schedule Vision

Predict what codes the coordinator will write in the schedule Excel, given what the database knows.

## The Problem

The database stores schedule assignments as generic codes (`C`, `OFF`, `NF`, `W`, `LV`, `GME`, etc.), but the coordinator's handjam Excel uses context-specific display codes (`CC`, `PedsNF`, `L&D`, `FMIT`, `Endo`, `AT`, `CCC`, etc.). The mapping depends on:

- **Rotation** (NF on a LDNF rotation = "L&D", NF on NF/ENDO = "NF")
- **Weekend vs weekday** (faculty GME on weekends = "W")
- **Person** (each faculty member has their own AT/GME/DO/CV pattern)
- **Sub-clinic type** (C on PROC = could be SIM, PR, US, Ophtho depending on the day)

Hand-coded rules capture ~53% of patterns. This project captures the rest by learning from historical handjam schedules.

## Current Accuracy (Block 10)

| Approach | Accuracy | Notes |
|----------|----------|-------|
| Raw DB codes | 28.6% | baseline |
| Hand-coded rules | 52.9% | 7 rule categories |
| **Hierarchical lookup** | **68.8%** | 6-level lookup from training data |

The remaining ~31% gap is deep coordinator knowledge: sub-clinic day assignments, NF/Endo confusion, and person-specific faculty codes.

**More historical schedules = higher accuracy.** Each block added to training data covers new (rotation, db_code, context) combinations the lookup table has never seen.

## How It Works

```
Handjam Excel           DB export JSON
     |                       |
     v                       v
  extract.py -----> features_all.json (labeled training data)
                           |
                    fill_template.py
                           |
                           v
                    Block Template2 Excel (filled with predictions)
```

1. `extract.py` reads the handjam workbook cell-by-cell, extracts what the coordinator wrote (truth) alongside what the DB would produce, plus visual features (cell color, font)
2. `fill_template.py` builds a hierarchical lookup table from all training data, then fills a blank BlockTemplate2 template with predicted codes

## Quick Start

```bash
cd ~/schedule-vision
source venv/bin/activate

# Generate a filled Block 10 Excel
python fill_template.py --truth data/features_all.json --output data/Block10.xlsx
open data/Block10.xlsx
```

## Files

### Core Pipeline

| File | Purpose |
|------|---------|
| `extract.py` | Extract features from handjam + DB → training data JSON |
| `fill_template.py` | Fill BlockTemplate2 template with predicted display codes |
| `learn.py` | Train RF classifier (research tool, not used in production) |
| `predict.py` | Apply trained RF model to new data (superseded by fill_template.py) |
| `compare.py` | HTML diff report comparing predictions vs ground truth |

### Research/Diagnostic

| File | Purpose |
|------|---------|
| `lookup.py` | Tested various lookup key strategies (informed fill_template.py) |
| `ensemble.py` | Tested RF + lookup ensemble approaches (all failed) |
| `ablation.py` | Feature ablation study for RF model |
| `diagnose.py` | LOBO failure analysis by person/rotation |
| `render.py` | Render schedule rows as PNG images |
| `discover.py` | VLM pattern discovery with local LLaVA (experimental) |

### Data

| File | Contents |
|------|----------|
| `data/features_all.json` | 6,400 cells from Blocks 7-10 with truth + DB + visual features |
| `data/model_all.pkl` | Trained RF model (190MB, not committed to git) |
| `data/Block10_ML.xlsx` | Latest generated Block 10 schedule |

## Adding Historical Schedules

**This is the single most impactful thing you can do to improve accuracy.** Each historical schedule block teaches the system new coordinator patterns.

### What You Need

For each historical block, you need TWO things:

1. **The handjam Excel** (the coordinator's manual schedule)
   - The `.xlsx` file the coordinator actually edits
   - Must have a tab named "Block N" (e.g., "Block 5", "Block 11")
   - Can be from any academic year — patterns carry across years

2. **A DB export JSON** for the same date range
   - Already exported for all AY 25-26 blocks: `/tmp/block{N}_data.json`
   - Contains the raw DB assignment codes before coordinator edits

### Ideal Historical Files

Ranked by impact (highest first):

| Priority | What | Why |
|----------|------|-----|
| 1 | **Blocks 2-6 from AY 25-26** (current handjam) | Same residents/faculty, but the handjam tabs use a different column layout (name in col 3 not col 5). Need extract.py update for 3-col format. |
| 2 | **Any complete AY handjam from prior years** (AY 24-25, 23-24, etc.) | Different residents but same faculty patterns, same rotation types. Each AY adds ~13 blocks of training data. |
| 3 | **Blocks 11-13 from current AY** | Currently empty in the handjam. Once the coordinator fills them, re-extract. |

### Step-by-Step: Adding a New Block

```bash
cd ~/schedule-vision
source venv/bin/activate

# 1. Extract features from the handjam + DB JSON
#    (The handjam path is wherever you saved the coordinator's Excel)
python extract.py \
    --workbook ~/Downloads/"Current AY 25-26 pulled 29 JAN 2026.xlsx" \
    --db-json /tmp/block9_data.json \
    --block "Block 9" \
    --output data/features_block9.json

# 2. Merge with existing training data
python -c "
import json
existing = json.loads(open('data/features_all.json').read())
new = json.loads(open('data/features_block9.json').read())
# Deduplicate by (person, block, day_index, half)
seen = set()
merged = []
for f in existing + new:
    key = (f.get('person'), f.get('block_number'), f.get('day_index'), f.get('half'))
    if key not in seen:
        seen.add(key)
        merged.append(f)
open('data/features_all.json', 'w').write(json.dumps(merged, indent=2))
print(f'Merged: {len(existing)} + {len(new)} → {len(merged)} (deduplicated)')
"

# 3. Re-generate the Excel with the expanded lookup table
python fill_template.py --truth data/features_all.json --output data/Block10.xlsx

# 4. (Optional) Retrain the RF model
python learn.py --features data/features_all.json --output data/model_all.pkl
```

### Adding a Whole Prior-Year Handjam

If you get a complete AY handjam (e.g., AY 24-25), extract all blocks at once:

```bash
# Extract all blocks that have data
python extract.py \
    --workbook ~/Downloads/"AY 24-25 Schedule.xlsx" \
    --blocks "Block 2" "Block 3" "Block 4" "Block 5" "Block 6" \
             "Block 7" "Block 8" "Block 9" "Block 10" "Block 11" "Block 12" "Block 13" \
    --db-dir /tmp/ \
    --output data/features_ay2425.json
```

**Note on DB exports for prior years:** You'll need to export DB JSON for the prior year's date ranges. If the DB doesn't have prior-year data, the extract still works — features will have `truth_code` (from the handjam) but no `db_code`, which means they contribute to the per-person lookup tables but not the rotation-based ones.

### What extract.py Needs from the Workbook

For Blocks 7-13 (current layout):
- **Column A**: Rotation 1 (e.g., "FMC", "NEURO", "NF")
- **Column B**: Rotation 2 (e.g., "MS: Endo") — may be merged with A
- **Column C**: Template code (R1/R2/R3/C19)
- **Column D**: Role (PGY 1/PGY 2/PGY 3/FAC)
- **Column E**: Name in "Last, First" format
- **Columns F onwards**: Schedule codes, 2 columns per day (AM/PM)
- **Row 3**: Dates
- **Rows 9-25**: Residents
- **Rows 31-44**: Faculty

For Blocks 2-6 (older layout): extract.py would need an update to handle 3-column identity format (name in col 3 instead of col 5). Not yet implemented.

## How the Lookup Table Works

The lookup table is a hierarchy of majority-vote tables built from training data:

```
Level 0: (person_last, db_code, weekday/weekend, half)    ← faculty only
Level 1: (rotation, db_code, weekday/weekend, person_type, half)
Level 2: (rotation, db_code, weekday/weekend, person_type)
Level 3: (rotation, db_code, weekday/weekend)
Level 4: (rotation, db_code)
Level 5: (db_code)
```

For each cell to predict, it tries Level 0 first (most specific), and falls back through the hierarchy until it finds a match. The per-person level (0) only applies to faculty because faculty maintain consistent patterns across blocks, while residents change rotations every block.

**Example:** A faculty member with DB code "GME" on a weekday PM:
- Level 0 looks up `("lastname", "GME", "wkday", "pm")` → finds "AT" from training data
- Without per-person level, it would fall through to Level 5: `("GME")` → "W" (wrong)

## fill_template.py Modes

```bash
# Default: hierarchical lookup (best accuracy)
python fill_template.py --truth data/features_all.json

# Rules only (no training data needed)
python fill_template.py --mode rules-only

# Hybrid: rules for definitive changes, lookup for the rest
python fill_template.py --mode hybrid-lookup --truth data/features_all.json

# ML model (requires trained model, worse than lookup without visual features)
python fill_template.py --mode ml-only
```

## What's Left (Remaining 31% Errors)

The errors fall into categories that require either more data or new features:

| Error Category | Count | Fix |
|----------------|-------|-----|
| Sub-clinic types (C→PR/SIM/US/CC/C40) | ~80 | More blocks with same rotations would teach the day-specific patterns |
| Faculty code confusion (GME↔AT, LV↔DEP↔USAFP) | ~70 | More prior-year handjams for per-person patterns |
| NF/Endo split (OFF→NF vs Endo) | ~16 | Specific rule for NF/ENDO rotation |
| Weekend NF false positives | ~16 | Tighten NF detection on NF/ENDO rotation weekends |
| PedsNF naming (PedW vs PedsNF) | ~8 | Normalize naming across blocks |

## Dependencies

```
pip install openpyxl scikit-learn numpy joblib Pillow
```

Or use the existing venv:
```bash
cd ~/schedule-vision
source venv/bin/activate
```
