# PRD: money-manager-auto-importer

## Problem

Manually entering Revolut transactions into Money Manager (RealByte) is tedious and error-prone.

## Solution

A Python script that takes a manually exported Revolut CSV, transforms it into Money Manager's CSV format, and outputs a ready-to-import file.

## Architecture

```
Revolut CSV Export ──> Python Script ──> CSV ──> Money Manager Import
```

## Core Requirements

| # | Requirement |
|---|---|
| 1 | Parse Revolut's exported CSV format |
| 2 | Map Revolut transaction fields to Money Manager CSV format |
| 3 | Auto-categorize transactions using keyword matching |
| 4 | Deduplicate — never import the same transaction twice |
| 5 | Output a CSV file compatible with Money Manager's import |
| 6 | Persist sync state (set of imported transaction IDs) |

## Money Manager CSV Schema

| Column | Source (Revolut CSV) | Format |
|---|---|---|
| Date | `Started Date` | MM/DD/YYYY |
| Account | Config value | e.g. "Revolut" |
| Category | Keyword map | Must match MM categories |
| Subcategory | Keyword map (optional) | |
| Note | `Description` | Transaction description |
| Amount | `Amount` | Absolute value |
| Income/Expense | Sign of `Amount` | "Income" if positive, "Expense" if negative |
| Currency | `Currency` | e.g. EUR |

## Category Mapping

User-defined rules in `config.yaml`, evaluated in order:

1. **Keyword match** — if description contains "Spotify" → Subscriptions
2. **Fallback** — "Uncategorized"

## Architectural Decisions

### Why manual CSV export instead of API?

Revolut offers two APIs — neither available for personal account holders:

- **Business API** — restricted to Revolut Business customers on paid plans (Grow+).
- **Open Banking API** — requires PSD2 registration as a licensed Third Party Provider (AISP/PISP) with a valid eIDAS certificate. Intended for regulated fintech companies, not individual developers.

Third-party aggregators (GoCardless, TrueLayer) require paid plans for live data access.

**Decision:** Use Revolut's built-in CSV export as input. The user exports transactions manually from the Revolut app, then runs the script to transform them. This keeps the project simple, free, and dependency-light.

## Tech Stack

- **Language:** Python 3.11+
- **Config:** YAML
- **State:** JSON file (set of imported transaction IDs)
- **Dependencies:** `pyyaml`, `csv` (stdlib)

## Out of Scope

- Automated transaction fetching via API (GoCardless, TrueLayer, Revolut API)
- Fully automated import into Money Manager (requires root or ADB)
- Real-time / push-based sync
- Multi-bank support (Revolut only for now)
- UI or web interface

## File Structure

```
money-manager-auto-importer/
├── config.yaml            # Account name, category rules
├── convert.py             # Entry point — run this
├── revolut_parser.py      # Parse Revolut CSV export
├── category_mapper.py     # Keyword → category logic
├── state.json             # Auto-managed dedup state
├── input/                 # Drop Revolut CSVs here
└── output/                # Generated CSVs
```

## Success Criteria

- Running `python convert.py` processes a Revolut CSV export and produces a valid Money Manager CSV
- CSV imports into Money Manager with correct dates, amounts, and categories
- No duplicate transactions after multiple runs