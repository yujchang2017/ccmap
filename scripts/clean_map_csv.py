"""Clean map.csv by removing fully blank rows.

This script removes rows where *all* columns are empty/whitespace.
It creates a timestamped .bak backup before overwriting the original file.

Usage:
  python scripts/clean_map_csv.py
  python scripts/clean_map_csv.py --input data/maps/map.csv
  python scripts/clean_map_csv.py --input data/maps/map.csv --output data/maps/map.cleaned.csv
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


def _is_blank_cell(value: object) -> bool:
    if value is None:
        return True
    # We read as strings, but keep this robust.
    text = str(value)
    return text.strip() == ""


def remove_fully_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    blank_row_mask = df.apply(lambda row: all(_is_blank_cell(v) for v in row.values), axis=1)
    return df.loc[~blank_row_mask].copy()


def remove_rows_blank_except_id(df: pd.DataFrame, id_columns: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    existing_id_cols = [c for c in id_columns if c in df.columns]
    if not existing_id_cols:
        raise ValueError(
            "None of the provided id columns exist in the CSV. "
            f"Provided={id_columns}, available={list(df.columns)}"
        )

    non_id_cols = [c for c in df.columns if c not in existing_id_cols]
    if not non_id_cols:
        # If the CSV only contains ID columns, nothing meaningful to keep.
        return df.iloc[0:0].copy()

    blank_except_id_mask = df[non_id_cols].apply(
        lambda row: all(_is_blank_cell(v) for v in row.values),
        axis=1,
    )
    return df.loc[~blank_except_id_mask].copy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove fully blank rows from map.csv")
    parser.add_argument(
        "--input",
        dest="input_path",
        default="data/maps/map.csv",
        help="Input CSV path (default: data/maps/map.csv)",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help="Output CSV path. If omitted, overwrites input (with .bak backup).",
    )
    parser.add_argument(
        "--id-columns",
        dest="id_columns",
        default="map_id,id,ID",
        help="Comma-separated ID column names to treat as the only-allowed nonblank fields (default: map_id,id,ID)",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    output_path = Path(args.output_path).resolve() if args.output_path else input_path

    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    # Read everything as strings so we can treat whitespace consistently.
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    original_rows = len(df)

    id_columns = [c.strip() for c in str(args.id_columns).split(",") if c.strip()]
    # First, remove "blank except ID" rows; this also removes fully blank rows.
    cleaned = remove_rows_blank_except_id(df, id_columns=id_columns)
    cleaned_rows = len(cleaned)
    removed = original_rows - cleaned_rows

    # Backup only when overwriting.
    if output_path == input_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = input_path.with_suffix(input_path.suffix + f".{timestamp}.bak")
        backup_path.write_bytes(input_path.read_bytes())
        print(f"Backup created: {backup_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Input:   {input_path}")
    print(f"Output:  {output_path}")
    print(f"Rows:    {original_rows} -> {cleaned_rows} (removed {removed})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
