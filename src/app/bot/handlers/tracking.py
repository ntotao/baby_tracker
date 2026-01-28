from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.event import EventService
from src.app.services.tenant import TenantService
import datetime

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        # Check tenant
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await update.message.reply_text("Non hai ancora un tracker. Usa /start.")
            return

        # Show Menu
        keyboard = [
            [InlineKeyboardButton("💩 Cacca", callback_data='track_cacca'),
             InlineKeyboardButton("💧 Pipì", callback_data='track_pipi')],
            [InlineKeyboardButton("💩+💧 Entrambi", callback_data='track_entrambi')],
            [InlineKeyboardButton("🍼 Allattamento", callback_data='track_allattamento')],
            [InlineKeyboardButton("📊 Stato Oggi", callback_data='view_status')]
        ]
        
        text = "Cosa vuoi registrare?"
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def track_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            return

        event_service = EventService(db)
        
        if data == 'track_cacca':
            await event_service.add_event(tenant.id, user_id, 'cacca')
            await query.edit_message_text("Registrato: 💩 Cacca!")
        elif data == 'track_pipi':
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.edit_message_text("Registrato: 💧 Pipì!")
        elif data == 'track_entrambi':
            await event_service.add_event(tenant.id, user_id, 'cacca')
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.edit_message_text("Registrato: 💩 Cacca & 💧 Pipì!")
        elif data == 'track_allattamento':
             # Here we could ask for side/duration, for MVP just log it
             await event_service.add_event(tenant.id, user_id, 'allattamento')
             await query.edit_message_text("Registrato: 🍼 Poppata!")
        
        elif data == 'view_status':
            await show_status(update, tenant.id, event_service)

async def show_status(update: Update, tenant_id: str, service: EventService):
    events = await service.get_recent_events(tenant_id, 10)
    summary = await service.get_daily_summary(tenant_id)
    
    # Format Summary
    summary_text = "📊 *Riepilogo Oggi:*\n"
    if not summary:
        summary_text += "Nessun evento oggi.\n"
    else:
        for etype, count in summary:
            icon = "❓"
            if etype == 'cacca': icon = "💩"
            elif etype == 'pipi': icon = "💧"
            elif etype == 'allattamento': icon = "🍼"
            summary_text += f"{icon} {etype.capitalize()}: {count}\n"
            
    # Format List
    events_text = "\n🕒 *Ultimi Eventi:*\n"
    for e in events:
        # Time formatting (naive + 1h for CET roughly, can improve)
        ts = e.timestamp.strftime("%H:%M")
        icon = "⚪️"
        if e.event_type == 'cacca': icon = "💩"
        elif e.event_type == 'pipi': icon = "💧"
        elif e.event_type == 'allattamento': icon = "🍼"
        events_text += f"{ts} {icon} {e.event_type}\n"

    msg = f"{summary_text}{events_text}"
    
    # Back button
    kb = [[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler(update, context)

# Handler Exports
menu_cmd_handler = CommandHandler("menu", menu_handler)
track_handler = CallbackQueryHandler(track_callback, pattern="^track_")
status_handler = CallbackQueryHandler(track_callback, pattern="^view_status$") # piggyback on track for service reuse or separate
back_handler = CallbackQueryHandler(back_to_menu, pattern="^menu_main$")
