import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from config import Settings, get_settings
from database import DbClient, get_db_client
from services import payment_service
from services.rate_limit_service import RateLimitRule, assert_rate_limit

router = APIRouter(prefix="/maintenance", tags=["maintenance"])
EXPIRE_PAYMENTS_LIMIT = RateLimitRule("maintenance:expire-payments", 10, 60)


@router.post("/payments/expire-pending")
def expire_pending_payments(
    request: Request,
    x_maintenance_secret: str | None = Header(default=None, alias="X-Maintenance-Secret", min_length=1, max_length=512),
    settings: Settings = Depends(get_settings),
    client: DbClient = Depends(get_db_client),
):
    assert_rate_limit(request, EXPIRE_PAYMENTS_LIMIT, identity_parts=[x_maintenance_secret])
    _require_maintenance_secret(settings, x_maintenance_secret)
    return payment_service.expire_abandoned_pending_online_payments(
        client,
        older_than_minutes=settings.payment_expiry_minutes,
    )


def _require_maintenance_secret(settings: Settings, supplied: str | None) -> None:
    expected = settings.payment_expiry_cron_secret
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payment expiry maintenance is not configured.")
    if supplied is None or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Maintenance access denied.")
