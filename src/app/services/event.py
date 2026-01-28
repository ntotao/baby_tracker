from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from src.app.db.models import Event
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(self, tenant_id: str, user_id: int, event_type: str, details: dict = {}) -> Event:
        new_event = Event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            details=details
        )
        self.db.add(new_event)
        await self.db.commit()
        await self.db.refresh(new_event)
        return new_event

    async def get_recent_events(self, tenant_id: str, limit: int = 20):
        stmt = select(Event).where(Event.tenant_id == tenant_id).order_by(desc(Event.timestamp)).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_daily_summary(self, tenant_id: str):
        # Allow naive datetimes assuming server time matches user expectation for MVP
        # Ideally we'd use user timezone. For now, assume "today" based on server time.
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(Event.event_type, func.count(Event.id))\
            .where(Event.tenant_id == tenant_id)\
            .where(Event.timestamp >= today)\
            .group_by(Event.event_type)
            
        result = await self.db.execute(stmt)
        return result.all()
