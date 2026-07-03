# Users API

An asynchronous **user management** service built with FastAPI: registration,
JWT authentication, email verification, role-based access control, user CRUD and
automatic cleanup of unverified accounts. Designed as an extensible,
production-ready **modular monolith**.

---

## Features

| Requirement | Status |
|---|---|
| Registration (email, password, optional first/last name, unique email, starts **unverified**) | ✅ |
| JWT authentication — access + refresh tokens | ✅ |
| `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh` | ✅ |
| Email verification (`POST /auth/verify`, code generation) | ✅ |
| Auto-delete of users unverified for > 2 days | ✅ (APScheduler) |
| Roles: **User** / **Admin** with per-endpoint access control | ✅ |
| `GET /me`, `GET /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` | ✅ |
| Async architecture, SQLAlchemy 2.0, PostgreSQL **or** SQLite | ✅ |
| Docker + docker-compose | ✅ |
| OpenAPI / Swagger UI with English `summary` / `description` | ✅ |

---

## Architecture (modular monolith)

The domain is split into two self-contained modules under `apps/`, sharing
generic infrastructure in `core/`:

```text
apps/
├── users/                     # User domain
│   ├── domain/roles.py        # Role enum (USER / ADMIN)
│   ├── models/user.py         # User model (email, verification, role, ...)
│   ├── schemas/               # UserRead, UserUpdate
│   ├── service/user.py        # CRUD + cleanup_unverified()
│   ├── api/router.py          # /me, /users, /users/{id}
│   └── admin/user.py          # SQLAdmin view
│
└── auth/                      # Authentication flows
    ├── models/                # RefreshToken, VerificationCode
    ├── schemas/               # Signup/Login/Verify, tokens
    ├── service/auth.py        # signup, login, refresh, verify, logout
    ├── utils/
    │   ├── jwt.py             # access/refresh token helpers
    │   ├── verification.py    # 6-digit code generator
    │   ├── email/             # EmailSender abstraction (console / smtp)
    │   └── admin_auth.py      # SQLAdmin session auth (admins only)
    ├── api/                   # router, get_current_user, require_role
    └── cli/create_admin.py    # `make createsuperuser`

core/                          # DB engine/session, settings, security, logging
bootstrap/                     # routers, admin, scheduler, events wiring
migrations/                    # Alembic
```

Layering: **api → service → model**. Routers are thin (HTTP only); business
logic lives in services; services never depend on FastAPI. `auth` depends on the
`users` domain model, not the other way around.

### Authentication

- **Access token** — short-lived JWT (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 15).
- **Refresh token** — opaque UUID persisted in `refresh_tokens`, valid for
  `REFRESH_TOKEN_EXPIRE_DAYS` (default 30). `POST /auth/logout` revokes it.
- `require_role(Role.ADMIN)` guards admin-only endpoints; `get_current_user`
  resolves the bearer token for authenticated ones.

### Email verification

At signup a 6-digit code is stored in `verification_codes` and delivered through
a pluggable `EmailSender` selected by `EMAIL_BACKEND`:

- `console` (default) — logs the code; no external dependency (dev).
- `smtp` — sends a real email via any SMTP provider. A free option is
  **[Brevo](https://www.brevo.com)** (300 emails/day); Gmail app passwords or
  SendGrid also work. Configure with the `SMTP_*` variables.

`POST /auth/verify` marks the user verified. Login is refused until verified.

### Auto-cleanup

On startup an APScheduler job (`bootstrap/scheduler.py`) runs hourly and deletes
users that are still unverified after `UNVERIFIED_RETENTION_DAYS` (default 2).
Admins are never affected.

> **Why APScheduler and not Celery?** No broker/worker is required, which keeps
> the single-process deployment simple. For higher scale the same
> `UserService.cleanup_unverified()` call can be moved into a Celery beat task
> without touching the business logic.

---

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | — | Register a new (unverified) user |
| POST | `/auth/login` | — | Obtain access + refresh tokens |
| POST | `/auth/refresh` | — | Refresh the access token |
| POST | `/auth/verify` | — | Verify email with the code |
| POST | `/auth/resend-code` | — | Resend a verification code |
| POST | `/auth/logout` | — | Revoke a refresh token |
| GET | `/me` | user | Current user profile |
| GET | `/users` | admin | Paginated list of users |
| GET | `/users/{id}` | admin | Get a user by ID |
| PATCH | `/users/{id}` | user¹ | Partial update |
| DELETE | `/users/{id}` | admin | Delete a user |

¹ A user may update their own profile; admins may update anyone. Changing
`role` / `is_active` requires admin rights.

Interactive docs: **`/docs`** (Swagger UI) and **`/redoc`**. Admin panel: **`/admin`**.

---

## Running

### With Docker

```bash
cp .env_example .env          # then edit values (SECRET_KEY, DB_*, ...)
docker compose up --build
docker compose exec backend poetry run alembic upgrade head
docker compose exec backend make createsuperuser
```

API on `http://localhost:${APP_PORT}` (default 8000).

### Locally

```bash
cp .env_example .env
poetry install
poetry run alembic upgrade head
make createsuperuser          # create an admin
make run                      # uvicorn main:app --reload
```

### Using SQLite instead of PostgreSQL

Migrations honour an optional `ALEMBIC_DATABASE_URL` override:

```bash
ALEMBIC_DATABASE_URL="sqlite:////absolute/path/app.db" poetry run alembic upgrade head
```

The models use dialect-aware types (`BigInteger`→`Integer`, `false()`/`true()`)
so the schema runs on both databases.

---

## Configuration

Key `.env` variables (see `.env_example` for the full list):

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | — | JWT signing key (**required**) |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | — | PostgreSQL connection |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Refresh token lifetime |
| `VERIFICATION_CODE_EXPIRE_MINUTES` | 30 | Verification code lifetime |
| `UNVERIFIED_RETENTION_DAYS` | 2 | Cleanup threshold |
| `EMAIL_BACKEND` | `console` | `console` or `smtp` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | — | SMTP provider (e.g. Brevo) |

---

## Development

```bash
make check      # ruff lint + mypy
make format     # ruff format + autofix
make migration m="describe change"   # autogenerate a migration
make migrate    m="describe change"   # generate + apply
```

---

## Deliberate simplifications

Where scope was intentionally reduced, the code says so in comments. In
particular:

- **Email delivery** ships with a `console` backend that logs the code; the
  `smtp` backend is production-ready but real deliverability (SPF/DKIM, retries,
  templating) is left to the provider. SMS verification would slot in as another
  `EmailSender`-style transport.
- **Refresh tokens** are single opaque values; rotation and refresh-token reuse
  detection would be the next hardening step.
- **Cleanup** runs in-process via APScheduler; see the note above on moving it to
  Celery for horizontal scale.
