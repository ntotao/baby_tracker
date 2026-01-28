from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import models here to ensure they are registered with metadata
# This is a common pattern to avoid circular imports when using Alembic/create_all
# immediately after importing Base

