#!/usr/bin/env python3
"""Entry point: converts Revolut CSV exports to Money Manager TSV."""

import csv
import glob
import json
import os
import shutil
import sys
from datetime import datetime

import yaml

import category_mapper
import revolut_parser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
STATE_PATH = os.path.join(ROOT, "state.json")
INPUT_DIR = os.path.join(ROOT, "input")
OUTPUT_DIR = os.path.join(ROOT, "output")

TSV_COLUMNS = [
    "Date",
    "Account",
    "Category",
    "Subcategory",
    "Note",
    "Amount",
    "Income/Expense",
    "Description",
]


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state() -> set:
    if not os.path.exists(STATE_PATH):
        return set()
    with open(STATE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("imported_ids", []))


def save_state(imported_ids: set) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"imported_ids": sorted(imported_ids)}, f, indent=2)


def find_input_files() -> list[str]:
    return sorted(glob.glob(os.path.join(INPUT_DIR, "*.csv")))


def build_output_path() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"import_{timestamp}.tsv")


def main() -> None:
    config = load_config()
    account = config.get("account", "Revolut")
    rules = config.get("category_rules", [])

    imported_ids = load_state()

    input_files = find_input_files()
    if not input_files:
        print(f"No CSV files found in {INPUT_DIR}/. Drop your Revolut export there and re-run.")
        sys.exit(0)

    new_transactions = []
    for filepath in input_files:
        print(f"Parsing {filepath}...")
        transactions = revolut_parser.parse(filepath)
        for tx in transactions:
            if tx["id"] in imported_ids:
                continue
            category, subcategory = category_mapper.map_category(tx["description"], rules)
            new_transactions.append({
                "Date": tx["date"],
                "Account": account,
                "Category": category,
                "Subcategory": subcategory,
                "Note": "",
                "Amount": tx["amount"],
                "Income/Expense": tx["income_expense"],
                "Description": tx["description"],
                "_id": tx["id"],
            })

    if not new_transactions:
        print("No new transactions to import.")
        sys.exit(0)

    output_path = build_output_path()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(new_transactions)

    # Persist dedup state
    for tx in new_transactions:
        imported_ids.add(tx["_id"])
    save_state(imported_ids)

    print(f"Wrote {len(new_transactions)} transaction(s) to {output_path}")

    onedrive_path = config.get("onedrive_upload_path")
    if onedrive_path:
        os.makedirs(onedrive_path, exist_ok=True)
        dest = shutil.copy2(output_path, onedrive_path)
        print(f"Copied to OneDrive: {dest}")


if __name__ == "__main__":
    main()
