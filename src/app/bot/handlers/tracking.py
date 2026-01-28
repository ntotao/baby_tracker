from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.event import EventService
from src.app.services.tenant import TenantService
import datetime
import logging

logger = logging.getLogger(__name__)

async def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💩 Cacca", callback_data='track_cacca'),
         InlineKeyboardButton("💧 Pipì", callback_data='track_pipi')],
        [InlineKeyboardButton("💩+💧 Entrambi", callback_data='track_entrambi')],
        [InlineKeyboardButton("🍼 Allattamento", callback_data='menu_feeding')],
        [InlineKeyboardButton("📊 Stato Oggi", callback_data='view_status')]
    ])

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        # Check tenant
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await update.message.reply_text("Non hai ancora un tracker. Usa /start.")
            return

        text = "👶 *Baby Tracker Control Panel*\nCosa vuoi registrare?"
        keyboard = await get_main_menu_keyboard()
        
        if update.callback_query:
            # If coming from Back button, edit
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def track_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await query.answer("Errore: Tenant non trovato", show_alert=True)
            return

        event_service = EventService(db)
        
        # --- QUICK ACTIONS (Toast Notification Only) ---
        if data == 'track_cacca':
            await event_service.add_event(tenant.id, user_id, 'cacca')
            await query.answer("💩 Cacca registrata!", show_alert=False) 
            # Do NOT edit message, keep menu open
            
        elif data == 'track_pipi':
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.answer("💧 Pipì registrata!", show_alert=False)
            
        elif data == 'track_entrambi':
            await event_service.add_event(tenant.id, user_id, 'cacca')
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.answer("💩+💧 Entrambi registrati!", show_alert=False)

        # --- SUB MENUS ---
        elif data == 'menu_feeding':
            await query.answer()
            await show_feeding_menu(update)
            
        elif data.startswith('feed_'):
            # Handle specific feeding types
            feed_type = data.replace('feed_', '') # left, right, bottle
            details = {'source': feed_type}
            
            # TODO: Future upgrade for duration/timer
            await event_service.add_event(tenant.id, user_id, 'allattamento', details)
            
            # Confirm and return to main menu
            await query.answer(f"🍼 Allattamento ({feed_type}) registrato!", show_alert=False)
            await menu_handler(update, context) # Go back to main
            
        elif data == 'view_status':
            await query.answer()
            await show_status(update, tenant.id, event_service)

async def show_feeding_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("Left 👈", callback_data='feed_left'),
         InlineKeyboardButton("Right 👉", callback_data='feed_right')],
        [InlineKeyboardButton("🍼 Biberon", callback_data='feed_bottle'),
         InlineKeyboardButton("🔄 Entrambi", callback_data='feed_both')],
        [InlineKeyboardButton("🔙 Indietro", callback_data='menu_main')]
    ]
    await update.callback_query.edit_message_text(
        "🍼 *Allattamento*\nScegli il dettaglio:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_status(update: Update, tenant_id: str, service: EventService):
    events = await service.get_recent_events(tenant_id, 10)
    summary = await service.get_daily_summary(tenant_id)
    
    # Format Summary
    summary_text = "📊 *Riepilogo Oggi:*\n"
    if not summary:
        summary_text += "Nessun evento oggi.\n"
    else:
        for etype, count in summary:
            icon = "⚪️"
            if etype == 'cacca': icon = "💩"
            elif etype == 'pipi': icon = "💧"
            elif etype == 'allattamento': icon = "🍼"
            summary_text += f"{icon} {etype.capitalize()}: {count}\n"
            
    # Format List
    events_text = "\n🕒 *Ultimi Eventi:*\n"
    for e in events:
        ts = e.timestamp.strftime("%H:%M") # Naive server time
        
        detail_str = ""
        if e.details and e.event_type == 'allattamento':
            src = e.details.get('source', '')
            if src == 'left': detail_str = " (👈)"
            elif src == 'right': detail_str = " (👉)"
            elif src == 'bottle': detail_str = " (🍼)"
            
        icon = "⚪️"
        if e.event_type == 'cacca': icon = "💩"
        elif e.event_type == 'pipi': icon = "💧"
        elif e.event_type == 'allattamento': icon = "🍼"
        
        events_text += f"`{ts}` {icon} {e.event_type}{detail_str}\n"

    msg = f"{summary_text}{events_text}"
    kb = [[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]]
    
    await update.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler(update, context)

# Handler Exports
menu_cmd_handler = CommandHandler("menu", menu_handler)
# Catch-all for track_, feed_, view_status
track_handler = CallbackQueryHandler(track_callback, pattern="^(track_|feed_|view_status)") 
back_handler = CallbackQueryHandler(back_to_menu, pattern="^menu_main$")
