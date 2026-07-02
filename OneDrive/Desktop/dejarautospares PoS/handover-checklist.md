# Handover Readiness Checklist

## Files
- [x] `.gitignore` excludes `.env` and `instance/`
- [x] `.env.example` exists with required variables
- [ ] `.env` created locally and never committed

## Security
- [x] `SECRET_KEY` sourced from environment
- [x] `SESSION_COOKIE_SECURE` can be enabled via `FORCE_HTTPS`
- [x] `SESSION_COOKIE_HTTPONLY` and `SESSION_COOKIE_SAMESITE=Lax`
- [x] CSRF protection enabled via `Flask-WTF`
- [x] Rate limiting configured; production should use Redis storage

## Testing
- [x] `pytest -q` passes
- [ ] Run smoke tests after final changes

## Deployment notes
- [x] SQLite default can be replaced by a managed database
- [x] `DATABASE_URL` supports absolute and relative SQLite paths
- [x] `FORCE_HTTPS=true` for production
- [ ] Confirm platform-specific deployment commands for target host
