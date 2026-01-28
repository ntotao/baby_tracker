from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService
import logging

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        
        if not tenant:
            msg = "Non hai un tracker attivo."
            if update.callback_query: await update.callback_query.answer(msg, show_alert=True)
            else: await update.message.reply_text(msg)
            return

        if str(tenant.admin_user_id) != str(user_id):
            msg = "⛔ Solo l'amministratore del tracker può accedere a questo pannello."
            if update.callback_query: await update.callback_query.answer(msg, show_alert=True)
            else: await update.message.reply_text(msg)
            return

        users_count = len(tenant.allowed_users) if tenant.allowed_users else 0
        
        msg = f"🛡️ *Pannello Admin*\n\n"
        msg += f"👤 *Admin:* `{tenant.admin_user_id}`\n"
        msg += f"👥 *Utenti Autorizzati:* {users_count}\n"
        msg += f"🆔 *Tenant ID:* `{tenant.id}`\n"
        
        keyboard = [
            [InlineKeyboardButton("🔗 Genera Link Invito", callback_data='admin_invite')],
            [InlineKeyboardButton("🔙 Menu Principale", callback_data='menu_main')]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'admin_invite':
        bot = await context.bot.get_me()
        bot_username = bot.username
        
        async with AsyncSessionLocal() as db:
             tenant_service = TenantService(db)
             tenant = await tenant_service.get_tenant_by_user(update.effective_user.id)
             invite_link = f"https://t.me/{bot_username}?start={tenant.id}"
             
             await query.answer()
             await query.edit_message_text(
                 f"🔗 *Link di Invito*\n\nInvia questo link al partner/familiare:\n`{invite_link}`\n\nQuando lo cliccheranno, verranno aggiunti al tuo tracker.",
                 parse_mode='Markdown',
                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin", callback_data='admin_panel')]])
             )
    elif data == 'admin_panel':
        await admin_panel(update, context)

admin_handler = CommandHandler("admin", admin_panel)
admin_callback_handler = CallbackQueryHandler(admin_actions, pattern='^admin_')
