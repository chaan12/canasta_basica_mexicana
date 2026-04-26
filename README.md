# Mexican Basic Basket Dashboard

Flask application for simulating biweekly household spending and comparing the Mexican basic basket across supermarkets.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

SQLite is created automatically in `instance/canasta_basica.db`. The app synchronizes the 24 basic basket products from `data/basic_basket.json` at startup.

## Importing the Spreadsheet

The spreadsheet is the source for product names, presentations, supermarket prices, cheapest store, average price, and price variance.

```bash
python3 scripts/import_catalog.py "/path/to/Hoja de cálculo sin título.xlsx"
```

The importer writes `data/basic_basket.json`. You can also set `BASKET_EXCEL_PATH` to force the app to read a spreadsheet directly at startup.

## Deployment Notes

1. Upload the project to the server.
2. Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the WSGI entry point to import `app` from `app.py`.
4. Reload the web application.
