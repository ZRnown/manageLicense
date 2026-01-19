# Repository Guidelines

## Project Structure & Module Organization
- `main.py` holds the FastAPI app, database initialization, and the admin HTML template.
- `requirements.txt` lists Python dependencies.
- `ecosystem.config.js` defines PM2 process settings.
- `start.sh` runs the development server with Uvicorn.
- `generate_license.sh` is a CLI helper to create license keys via the admin endpoint.
- `logs/` stores runtime logs (created on demand).
- `licenses.db` is the SQLite database created at runtime; keep it local.
- `CLIENT_GUIDE.md` and `README.md` document usage.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs Python dependencies.
- `uvicorn main:app --host 0.0.0.0 --port 8000` starts the API locally.
- `./start.sh` is a shortcut for the Uvicorn command above.
- `pm2 start ecosystem.config.js` runs the server under PM2 (production-style).
- `./generate_license.sh 5 -1 "VIP客户" "your_secret_password"` generates keys through the admin endpoint.

## Coding Style & Naming Conventions
- Use 4-space indentation and standard Python formatting.
- Follow `snake_case` for functions/variables and `UPPER_SNAKE_CASE` for constants (for example, `ADMIN_PASSWORD`).
- Keep database schema changes inside `init_db()` in `main.py` to avoid drift.

## Testing Guidelines
- No automated tests exist yet.
- For manual checks, use `curl` or the admin UI. Example:
  `curl -X POST http://localhost:8000/api/activate -H 'Content-Type: application/json' -d '{"key":"...","hwid":"..."}'`.
- If you add tests, prefer `pytest` and name files `test_*.py`.

## Commit & Pull Request Guidelines
- Use short, imperative commit messages (for example, "Add startup script").
- PRs should include a concise summary, how you verified changes, and screenshots for admin UI changes.
- Link relevant issues and update docs when behavior changes.

## Security & Configuration Tips
- Set a strong `ADMIN_PASSWORD` in `main.py` before deployment.
- Do not commit `licenses.db` or log files; back them up separately.
- Use HTTPS and a reverse proxy (like Nginx) in production.
