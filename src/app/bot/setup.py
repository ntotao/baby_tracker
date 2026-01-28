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
    from src.app.bot.handlers.tracking import menu_cmd_handler, track_handler, back_handler, status_cmd_handler, help_cmd_handler
    from src.app.bot.handlers.profile import profile_conv_handler
    from src.app.bot.handlers.manual_log import manual_log_handler
    from src.app.bot.handlers.admin import admin_handler, admin_callback_handler
    from src.app.bot.handlers.history import history_cmd_handler, history_callback_handler
    from src.app.bot.handlers.import_export import import_handler
    from src.app.bot.handlers.charts import chart_handler
    
    app.add_handler(start_handler)
    app.add_handler(register_handler)
    app.add_handler(profile_conv_handler)
    app.add_handler(manual_log_handler)
    app.add_handler(import_handler)
    app.add_handler(chart_handler)
    app.add_handler(admin_handler)
    app.add_handler(admin_callback_handler)
    app.add_handler(history_cmd_handler)
    app.add_handler(history_callback_handler) # BEFORE track_handler if possible, or track_handler pattern specific?
    # track_handler has pattern "^(track_|feed_|view_status|menu_|delete_)"
    # history has "^hist_"
    # So no partial overlapping. Safe.
    app.add_handler(CommandHandler("invite", invite_command))
    app.add_handler(menu_cmd_handler)
    app.add_handler(status_cmd_handler)
    app.add_handler(help_cmd_handler)
    app.add_handler(track_handler)
    app.add_handler(back_handler)
    
    return app
