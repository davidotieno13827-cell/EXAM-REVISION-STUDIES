# Dejar Auto Spares POS

This is a Flask-based Point of Sale application for managing auto parts and lubricant inventory.

## Features
- Inventory management
- Low-stock alerts
- Sales recording
- Sales and inventory export (CSV)
- Excel price list display in add-product page
- Login-protected admin actions

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy the environment template and configure `.env` values:
   ```bash
   copy .env.example .env
   ```
   `.env` is already ignored by `.gitignore`.
3. Initialize the database:
   ```bash
   python create_db.py
   ```
4. Start the app:
   ```bash
   python run.py
   ```

## Testing
Run the pytest suite from the project root:
```bash
.venv\Scripts\pytest.exe
```

To run a single test file:
```bash
.venv\Scripts\pytest.exe tests/test_app.py
```

## Default admin credentials
The default admin user is seeded from your `.env` file via:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

## Deployment and handover notes
- Keep `.env` out of source control; use `.env.example` as the template.
- The default database is SQLite at `instance/app.db`.
- The app is served locally at `http://localhost:5000` and can be accessed on the local network if the host machine is reachable.
- For production, set `FORCE_HTTPS=true`, use a managed SQL database, and use a Redis URI for `RATE_LIMIT_STORAGE_URI` instead of in-memory rate limiting.
- Run `pytest -q` after changes to confirm the application remains healthy.
