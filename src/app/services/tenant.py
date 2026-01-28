from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.app.db.models import Tenant
from src.app.db.models import generate_uuid
import logging
import json

logger = logging.getLogger(__name__)

class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_by_user(self, user_id: int) -> Tenant | None:
        """
        Finds a tenant where the user is either the admin or in the allowed_users list.
        For MVP we just check if they are the admin or explicitly in list.
        Since allowed_users is JSON list, we might need a more complex query or just fetch relevant ones.
        For V1 optimization: Just find by admin_id first.
        """
        # Simple check: is admin?
        stmt = select(Tenant).where(Tenant.admin_user_id == user_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant
            
        # If not admin, we'd need to search all tenants (inefficient) or have a UserTenant mapping table.
        # For V1 MVP, we stick to "Creator is Admin". 
        # TODO: Implement UserTenant association table for efficient lookup in V2.
        return None

    async def create_tenant(self, user_id: int) -> Tenant:
        new_tenant = Tenant(
            admin_user_id=user_id,
            allowed_users=[user_id]
        )
        self.db.add(new_tenant)
        await self.db.commit()
        await self.db.refresh(new_tenant)
        return new_tenant
