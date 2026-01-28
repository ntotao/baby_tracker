from telegram.ext import Application, ApplicationBuilder, CommandHandler
from src.app.core.config import settings

async def create_bot() -> Application:
    """
    Creates and authenticates the Telegram Bot Application.
    """
    if not settings.TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in environment variables.")
        
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    
    # Register handlers
    from src.app.bot.handlers.onboarding import start_handler, register_handler, invite_command
    from src.app.bot.handlers.tracking import menu_cmd_handler, track_handler, back_handler
    
    app.add_handler(start_handler)
    app.add_handler(register_handler)
    app.add_handler(CommandHandler("invite", invite_command))
    app.add_handler(menu_cmd_handler)
    app.add_handler(track_handler)
    app.add_handler(back_handler)
    
    return app
