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
        
        # Check for Invite Payload
        if context.args and context.args[0].startswith("invite_"):
            # Format: invite_<tenant_id>
            try:
                invite_code = context.args[0]
                tenant_id_to_join = invite_code.replace("invite_", "")
                
                success = await service.add_user_to_tenant(tenant_id_to_join, user.id)
                if success:
                    await update.message.reply_text(f"✅ Ti sei unito al tracker `{tenant_id_to_join}`! 👪")
                    # Fallthrough to show menu
                else:
                    await update.message.reply_text("❌ Invito non valido o scaduto.")
            except Exception as e:
                await update.message.reply_text("❌ Errore durante l'adesione.")

        tenant = await service.get_tenant_by_user(user.id)
        
        if tenant:
            keyboard = [[InlineKeyboardButton("📋 Menu Principale", callback_data="menu_main")]]
            await update.message.reply_text(
                f"Bentornato! 👶\nTracker ID: `{tenant.id}`\nInvita qualcuno con /invite",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📝 Crea Nuovo Tracker", callback_data="register_new")]
            ]
            await update.message.reply_text(
                "Ciao! Benvenuto su Baby Tracker. \nSembra che tu non abbia ancora un tracker attivo.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        service = TenantService(db)
        tenant = await service.get_tenant_by_user(user_id)
        
        if not tenant:
            await update.message.reply_text("Devi prima creare un tracker!")
            return
            
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start=invite_{tenant.id}"
        
        await update.message.reply_text(
            f"👪 **Invita un genitore**\n\nCondividi questo link per dare accesso al tuo tracker:\n`{link}`",
            parse_mode='Markdown'
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
