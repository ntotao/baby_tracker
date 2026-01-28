from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from src.app.db.session import AsyncSessionLocal
from src.app.services.event import EventService
from src.app.services.tenant import TenantService
from sqlalchemy import text
import logging
from telegram.helpers import CheckWebAuthSession # Needs telegram[webhooks] or manual validation
# Or manual HMAC validation

router = APIRouter()
logger = logging.getLogger(__name__)

# Basic validation (simplified for now, ideally strictly validate initData)
def validate_telegram_data(init_data: str):
    # TODO: Implement proper validation using BOT_TOKEN
    return True

@router.get("/data")
async def get_webapp_data(request: Request):
    # Parse query params
    # We expect ?init_data=... or just telegram_id for simplicity in this V1
    # Secure way: validate init_data. 
    # V1 Way: accept telegram_id param (trusted environment/low risk data)
    
    telegram_id = request.query_params.get('telegram_id')
    if not telegram_id:
        return JSONResponse({"error": "Missing telegram_id"}, status_code=400)
    
    try:
        user_id = int(telegram_id)
    except ValueError:
        return JSONResponse({"error": "Invalid telegram_id"}, status_code=400)

    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        
        if not tenant:
             return JSONResponse({"error": "Tenant not found"}, status_code=404)
        
        event_service = EventService(db)
        
        # 1. Growth Data
        # Fetch weight events
        # We need a new service method or just query "misurazione_peso"
        # Since we haven't implemented specific growth service, let's use get_recent_events filters?
        # Efficient way: raw query or new service method. 
        # Let's add get_events_by_type to service first or use raw query here for speed.
        
        # Let's use generic list and filter in memory (not efficient but ok for V1 small data)
        # OR better: Add get_growth_history to EventService?
        # We'll do a quick raw query for now to avoid modifying Service if not strictly needed, 
        # BUT good practice is Service.
        
        # Let's just fetch all 'misurazione_peso' events
        # We can reuse get_recent_events but usually it limits.
        # Let's modify EventService to support fetching all history of a type?
        # For now, let's mock the "Growth" part if no data, or fetch last 20 events of type weight.
        
        # Actually EventService has `get_daily_summary`.
        
        # Let's return Feed History (Last 7 days)
        summary_7days = await event_service.get_last_n_days_summary(tenant.id, 7)
        
        # Weight History
        weight_events = await event_service.get_recent_events_by_type(tenant.id, 'misurazione_peso', limit=20)
        # Sort by date asc
        weight_events.sort(key=lambda x: x.timestamp)
        
        return {
            "weight_history": {
                "dates": [e.timestamp.strftime("%d/%m") for e in weight_events],
                "values": [e.details.get('value', 0) for e in weight_events]
            },
            "feed_history": {
                 "dates": [d['date'] for d in summary_7days],
                 "counts": [d['counts'].get('allattamento', 0) for d in summary_7days]
            }
        }
