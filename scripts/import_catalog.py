import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.catalog_importer import DEFAULT_CATALOG_PATH, parse_excel_catalog, save_catalog


def main():
    parser = argparse.ArgumentParser(description="Import the basic basket spreadsheet into JSON.")
    parser.add_argument("excel_path", help="Path to the source .xlsx file.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_CATALOG_PATH),
        help="Output JSON path.",
    )
    args = parser.parse_args()

    catalog = parse_excel_catalog(Path(args.excel_path))
    output_path = save_catalog(catalog, Path(args.output))
    print(f"Imported {len(catalog['products'])} products and {len(catalog['stores'])} stores into {output_path}.")


if __name__ == "__main__":
    main()
