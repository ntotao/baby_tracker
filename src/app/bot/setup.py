from telegram.ext import Application, ApplicationBuilder
from src.app.core.config import settings

async def create_bot() -> Application:
    """
    Creates and authenticates the Telegram Bot Application.
    """
    if not settings.TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in environment variables.")
        
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    
    # Register handlers
    from src.app.bot.handlers.onboarding import start_handler, register_handler
    app.add_handler(start_handler)
    app.add_handler(register_handler)
    
    return app
