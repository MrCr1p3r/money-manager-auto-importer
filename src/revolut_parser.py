import csv
from datetime import datetime


REVOLUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
OUTPUT_DATE_FORMAT = "%m/%d/%Y %H:%M"


def parse(filepath: str) -> list[dict]:
    """Parse a Revolut CSV export and return a list of transaction dicts."""
    transactions = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip pending or failed transactions
            if row.get("State", "").strip().upper() not in ("COMPLETED", ""):
                continue
            transactions.append(_transform(row))
    return transactions


def _transform(row: dict) -> dict:
    raw_date = row["Started Date"].strip()
    try:
        date = datetime.strptime(raw_date, REVOLUT_DATE_FORMAT)
    except ValueError:
        # Fallback: date-only format
        date = datetime.strptime(raw_date[:10], "%Y-%m-%d")

    amount = float(row["Amount"].strip())
    fee = float(row.get("Fee", "0").strip() or "0")

    return {
        "id": _make_id(row),
        "date": date.strftime(OUTPUT_DATE_FORMAT),
        "description": row["Description"].strip(),
        "amount": abs(amount) + fee,
        "income_expense": "Income" if amount >= 0 else "Expense",
    }


def _make_id(row: dict) -> str:
    """Stable unique ID for deduplication based on key fields."""
    parts = [
        row.get("Started Date", "").strip(),
        row.get("Description", "").strip(),
        row.get("Amount", "").strip(),
    ]
    return "|".join(parts)
