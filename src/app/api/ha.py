from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.session import get_db
from src.app.services.tenant import TenantService
from src.app.services.event import EventService
from src.app.core.config import settings
import datetime

router = APIRouter()

# Schemas
class HAEventRequest(BaseModel):
    telegram_id: int
    event_type: str
    details: dict = {}

class HAStatusResponse(BaseModel):
    tenant_name: str
    last_feed: str | None
    last_feed_side: str | None
    last_cacca: str | None
    last_pipi: str | None
    count_feed: int
    count_cacca: int
    count_pipi: int

@router.get("/status", response_model=HAStatusResponse)
async def get_ha_status(
    telegram_id: int = Query(..., description="User Telegram ID to identify Tenant"),
    db: AsyncSession = Depends(get_db)
):
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant_by_user(telegram_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found for this user")
        
    event_service = EventService(db)
    
    # Fetch Last events
    last_feed = await event_service.get_last_event_by_type(tenant.id, 'allattamento')
    last_cacca = await event_service.get_last_event_by_type(tenant.id, 'cacca')
    last_pipi = await event_service.get_last_event_by_type(tenant.id, 'pipi')
    
    # Fetch Today Summary
    summary = await event_service.get_daily_summary(tenant.id)
    counts = {s[0]: s[1] for s in summary}
    
    # Format Response
    now = datetime.datetime.now()
    
    def format_ts(evt):
        if not evt: return None
        # Return ISO string or human diff? HA prefers absolute state usually
        return evt.timestamp.isoformat()
    
    resp = HAStatusResponse(
        tenant_name=tenant.name,
        last_feed=format_ts(last_feed),
        last_feed_side=last_feed.details.get('source') if last_feed and last_feed.details else None,
        last_cacca=format_ts(last_cacca),
        last_pipi=format_ts(last_pipi),
        count_feed=counts.get('allattamento', 0),
        count_cacca=counts.get('cacca', 0),
        count_pipi=counts.get('pipi', 0)
    )
    return resp

@router.post("/event")
async def post_ha_event(
    payload: HAEventRequest,
    db: AsyncSession = Depends(get_db)
):
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant_by_user(payload.telegram_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    event_service = EventService(db)
    
    # Add event
    await event_service.add_event(
        tenant_id=tenant.id,
        user_id=payload.telegram_id,
        event_type=payload.event_type,
        details=payload.details
    )
    
    return {"status": "success", "message": f"{payload.event_type} added"}
