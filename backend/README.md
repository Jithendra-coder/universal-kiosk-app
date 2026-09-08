# Universal Kiosk FastAPI Backend

## Local Setup

This backend now uses local PostgreSQL plus JWT authentication.

Create your local env file from the safe template:

```powershell
Copy-Item .env.example .env
```

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/universal_kiosk_app
JWT_SECRET=replace-with-a-long-random-secret-at-least-32-characters
JWT_ACCESS_TOKEN_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
PUBLIC_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:3000
ALLOW_DEV_AUTH_BYPASS=false
PORT=8000

# Optional email delivery for welcome, reset-password, and staff-invite emails
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=MenuTap
SMTP_USE_TLS=true
DEV_EXPOSE_RESET_LINKS=false
EMAIL_OUTBOX_DIR=email_outbox

# Optional Redis cache for public kiosk menu reads
REDIS_URL=redis://localhost:6379/0
REDIS_MENU_TTL_SECONDS=120

# Optional Pexels picker for admin product and offer images
PEXELS_API_KEY=your-pexels-api-key
PEXELS_PER_PAGE=12
```

Create the database, then run:

```powershell
psql "$env:DATABASE_URL" -f backend/postgres_schema.sql
```

Install and run:

```powershell
venv\Scripts\pip.exe install -r requirements.txt
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Main API Areas

- `POST /api/auth/signup`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/businesses/{business_id}/staff`
- `POST /api/businesses/{business_id}/staff`
- `GET /api/onboarding/status`
- `GET /api/businesses/me`
- `POST /api/businesses`
- `PATCH /api/businesses/{business_id}`
- `GET /api/kiosk/{business_slug}/menu`
- `POST /api/kiosk/{business_slug}/orders`
- `GET /api/businesses/{business_id}/orders/active`
- `PATCH /api/orders/{order_id}/status`
- `GET /api/businesses/{business_id}/dashboard`
- `POST /api/businesses/{business_id}/uploads/product-image`
- `GET /api/media/pexels/search?q=pizza`

Authenticated admin/kitchen endpoints use the httpOnly `menutap_admin_session` cookie set by `/api/auth/login` and `/api/auth/verify-email`. `Authorization: Bearer <jwt_access_token>` remains a temporary compatibility fallback for non-browser clients.
Uploaded images are stored locally under `backend/uploads` and served from `/uploads`.

Signup verification codes, password reset links, welcome emails, and staff invites are sent by SMTP when SMTP variables are configured. In local development, when SMTP is missing or fails, email content is also written to `backend/email_outbox`, signup returns a local `dev_otp`, and password reset returns a local reset-page link. Redis is optional; when `REDIS_URL` is not set, the kiosk menu APIs continue to read directly from PostgreSQL. Pexels image search is optional; add `PEXELS_API_KEY` only when you want owners to pick images from Pexels inside the admin menu.
