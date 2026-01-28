from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService
from src.app.services.event import EventService
from src.app.db.models import Event
from sqlalchemy import select, desc
import logging

logger = logging.getLogger(__name__)

async def history_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    user_id = update.effective_user.id
    ITEMS_PER_PAGE = 5
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await update.message.reply_text("Nessun tracker attivo.")
            return

        # Fetch events with pagination
        offset = page * ITEMS_PER_PAGE
        stmt = select(Event).where(Event.tenant_id == tenant.id).order_by(desc(Event.timestamp)).limit(ITEMS_PER_PAGE).offset(offset)
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        # Check if there are more
        stmt_next = select(Event.id).where(Event.tenant_id == tenant.id).order_by(desc(Event.timestamp)).limit(1).offset(offset + ITEMS_PER_PAGE)
        result_next = await db.execute(stmt_next)
        has_next = result_next.scalar_one_or_none() is not None

    if not events and page == 0:
        msg = "📜 *Storico Eventi*\nNessun evento registrato."
        kb = [[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]]
    else:
        msg = f"📜 *Storico Eventi (Pagina {page + 1})*\n\n"
        keyboard = []
        
        for e in events:
            time_str = e.timestamp.strftime('%d/%m %H:%M')
            icon = "⚪️"
            if e.event_type == 'cacca': icon = "💩"
            elif e.event_type == 'pipi': icon = "💧"
            elif e.event_type == 'allattamento': icon = "🍼"
            elif 'misurazione' in e.event_type: icon = "⚖️"
            
            # Detail summary
            detail_txt = ""
            if e.details:
                if 'source' in e.details:
                    src = e.details['source']
                    if src == 'left': detail_txt = "Left"
                    elif src == 'right': detail_txt = "Right"
                    elif src == 'bottle': detail_txt = f"{e.details.get('quantity_ml', '?')}ml"
                if 'value' in e.details:
                    detail_txt = str(e.details['value'])
            
            row_text = f"{icon} {time_str} {detail_txt}"
            msg += f"{row_text}\n"
            
            # Button to delete this specific event
            keyboard.append([
                InlineKeyboardButton(f"🗑️ Cancella {time_str}", callback_data=f'hist_del_{e.id}')
            ])

        # Pagination controls
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prec.", callback_data=f'hist_page_{page-1}'))
        if has_next:
            nav_row.append(InlineKeyboardButton("Succ. ➡️", callback_data=f'hist_page_{page+1}'))
        
        if nav_row:
            keyboard.append(nav_row)
            
        keyboard.append([InlineKeyboardButton("🔙 Menu", callback_data='menu_main')])
        kb = keyboard

    markup = InlineKeyboardMarkup(kb)
    
    if update.callback_query:
        await update.callback_query.answer() # Ack immediately
        await update.callback_query.edit_message_text(msg, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(msg, reply_markup=markup, parse_mode='Markdown')

async def history_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith('hist_page_'):
        page = int(data.replace('hist_page_', ''))
        await history_list(update, context, page)
        
    elif data.startswith('hist_del_'):
        event_id = int(data.replace('hist_del_', ''))
        
        async with AsyncSessionLocal() as db:
            event = await db.get(Event, event_id)
            if event:
                await db.delete(event)
                await db.commit()
                await query.answer("✅ Evento eliminato!")
            else:
                await query.answer("⚠️ Evento non trovato o già eliminato.", show_alert=True)
        
        # Refresh current page (default 0 or try to guess? keep 0 simplicity)
        await history_list(update, context, 0)

history_cmd_handler = CommandHandler("history", lambda u, c: history_list(u, c, 0))
history_callback_handler = CallbackQueryHandler(history_action, pattern='^hist_')
