from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


GENERIC_ADDRESS = "TP. Hồ Chí Minh, Việt Nam"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore detailed restaurant addresses from HCM_data.csv.")
    parser.add_argument(
        "--hcm-data",
        default=str(Path(__file__).resolve().parents[3] / "HCM_data.csv"),
        help="Path to source HCM_data.csv.",
    )
    parser.add_argument(
        "--restaurants",
        default=str(Path(__file__).resolve().parents[1] / "data" / "restaurants.csv"),
        help="Path to backend restaurants.csv.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hcm_path = Path(args.hcm_data)
    restaurants_path = Path(args.restaurants)

    hcm_rows = _read_csv(hcm_path)
    restaurant_rows = _read_csv(restaurants_path)
    hcm_by_key: dict[tuple[str, float, float], list[dict[str, str]]] = defaultdict(list)
    for row in hcm_rows:
        hcm_by_key[_match_key(row)].append(row)

    restored = 0
    unmatched: list[str] = []
    for row in restaurant_rows:
        if row.get("address") != GENERIC_ADDRESS:
            continue
        matches = hcm_by_key.get(_match_key(row), [])
        if len(matches) != 1:
            unmatched.append(row.get("name", ""))
            continue

        source = matches[0]
        row["address"] = source["address"]
        row["description"] = source["description"] or row.get("description", "")
        restored += 1

    _write_csv(restaurants_path, restaurant_rows, restaurant_rows[0].keys())
    print(
        {
            "restaurant_rows": len(restaurant_rows),
            "hcm_rows": len(hcm_rows),
            "restored": restored,
            "unmatched": len(unmatched),
            "remaining_generic": sum(1 for row in restaurant_rows if row.get("address") == GENERIC_ADDRESS),
        }
    )
    if unmatched:
        print({"unmatched_samples": unmatched[:10]})


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _match_key(row: dict[str, str]) -> tuple[str, float, float]:
    return (
        row["name"].strip(),
        round(float(row["latitude"]), 7),
        round(float(row["longitude"]), 7),
    )


if __name__ == "__main__":
    main()
