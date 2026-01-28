from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as db:
        service = TenantService(db)
        tenant = await service.get_tenant_by_user(user.id)
        
        if tenant:
            await update.message.reply_text(
                f"Bentornato! 👶\nUse /menu per tracciare.\nTenant ID: `{tenant.id}`",
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📝 Crea Nuovo Tracker", callback_data="register_new")]
            ]
            await update.message.reply_text(
                "Ciao! Benvenuto su Baby Tracker. \nSembra che tu non abbia ancora un tracker attivo.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "register_new":
        user_id = query.from_user.id
        async with AsyncSessionLocal() as db:
            service = TenantService(db)
            # check again to be safe
            if await service.get_tenant_by_user(user_id):
                 await query.edit_message_text("Hai già un tracker!")
                 return

            tenant = await service.create_tenant(user_id)
            await query.edit_message_text(
                f"✅ Tracker creato con successo!\nID: `{tenant.id}`\n\nPuoi iniziare a tracciare.",
                parse_mode='Markdown'
            )

start_handler = CommandHandler("start", start)
register_handler = CallbackQueryHandler(register_callback, pattern="^register_new$")
