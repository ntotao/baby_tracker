from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.app.core.config import settings
from src.app.bot.setup import create_bot
import logging

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global bot state
bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle Bot startup/shutdown alongside FastAPI.
    """
    global bot_app
    logger.info("Starting Baby Tracker Bot...")
    
    try:
        # Initialize DB (Dev Mode: Create tables if not exist)
        # In Prod, we use Alembic. Here we do a quick init for the user.
        from src.app.db.base import Base
        from src.app.db.session import engine
        from src.app.db.models import Tenant, Event  # Import to register
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Initialize Bot
        bot_app = await create_bot()
        await bot_app.initialize()
        
        # Start Polling (for Development) or Webhook (for Prod)
        # For now, we assume simple polling loop handled manually or background task
        # But properly in ASGI, we start it here.
        if settings.DEBUG:
            logger.info("Starting polling...")
            await bot_app.start()
            # In a real ASGI setting, updater.start_polling() runs in a background thread 
            # or we manage updates via webhook endpoint. 
            # For simplicity in V1 Foundation, we start polling.
            await bot_app.updater.start_polling()
        else:
             # Webhook logic would go here
             pass
             
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
        
    finally:
        logger.info("Shutting down bot...")
        if bot_app and bot_app.updater.running:
            await bot_app.updater.stop()
        if bot_app:
            await bot_app.stop()
            await bot_app.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot_running": bot_app is not None}

@app.get("/")
async def root():
    return {"message": "Baby Tracker Bot API is running"}
