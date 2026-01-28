from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.event import EventService
from src.app.services.tenant import TenantService
import datetime
import logging

logger = logging.getLogger(__name__)

# States
SELECT_TYPE, SELECT_TIME, INPUT_CUSTOM_TIME = range(3)

async def manual_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💩 Cacca", callback_data='manual_type_cacca'),
         InlineKeyboardButton("💧 Pipì", callback_data='manual_type_pipi')],
        [InlineKeyboardButton("👈 Tetta SX", callback_data='manual_type_feed_left'),
         InlineKeyboardButton("👉 Tetta DX", callback_data='manual_type_feed_right')],
        [InlineKeyboardButton("🍼 Biberon", callback_data='manual_type_feed_bottle')],
        [InlineKeyboardButton("❌ Annulla", callback_data='manual_cancel')]
    ]
    
    text = "📝 *Inserimento Manuale*\nCosa vuoi registrare?"
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
    return SELECT_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'manual_cancel':
        await query.edit_message_text("Operazione annullata.")
        return ConversationHandler.END
        
    event_type_raw = data.replace('manual_type_', '')
    
    # Map raw type to event_type + details
    event_type = 'generic'
    details = {}
    
    if event_type_raw == 'cacca':
        event_type = 'cacca'
    elif event_type_raw == 'pipi':
        event_type = 'pipi'
    elif event_type_raw.startswith('feed_'):
        event_type = 'allattamento'
        source = event_type_raw.replace('feed_', '')
        details = {'source': source, 'manual': True}
        
    context.user_data['manual_event'] = {
        'type': event_type,
        'details': details
    }
    
    keyboard = [
        [InlineKeyboardButton("Adesso", callback_data='manual_time_now')],
        [InlineKeyboardButton("-15 min", callback_data='manual_time_15'),
         InlineKeyboardButton("-30 min", callback_data='manual_time_30')],
        [InlineKeyboardButton("-1 ora", callback_data='manual_time_60'),
         InlineKeyboardButton("-2 ore", callback_data='manual_time_120')],
        [InlineKeyboardButton("✍️ Scrivi Ora", callback_data='manual_time_custom')],
        [InlineKeyboardButton("❌ Annulla", callback_data='manual_cancel')]
    ]
    
    await query.edit_message_text(
        f"Hai scelto: *{event_type_raw.replace('_', ' ').capitalize()}*\nQuando è successo?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return SELECT_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'manual_cancel':
        await query.edit_message_text("Operazione annullata.")
        return ConversationHandler.END
        
    if data == 'manual_time_custom':
        await query.edit_message_text(
            "✍️ Scrivi l'orario nel formato `HH:MM` (per oggi) o `GG/MM HH:MM` (per altri giorni).\nEs: `14:30` o `27/01 10:00`",
            parse_mode='Markdown'
        )
        return INPUT_CUSTOM_TIME
        
    # Calculate time
    minutes_ago = 0
    if data != 'manual_time_now':
        minutes_ago = int(data.replace('manual_time_', ''))
        
    timestamp = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    return await save_event(update, context, timestamp)

async def input_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    now = datetime.datetime.now()
    
    try:
        timestamp = None
        if len(text) <= 5: # HH:MM
            t = datetime.datetime.strptime(text, "%H:%M").time()
            timestamp = datetime.datetime.combine(now.date(), t)
            # If time is in future, assume yesterday? No, just keep as is (user might prompt correction)
            if timestamp > now:
                timestamp = timestamp - datetime.timedelta(days=1)
        else: # DD/MM HH:MM
            # Assume current year
            dt = datetime.datetime.strptime(text + f" {now.year}", "%d/%m %H:%M %Y")
            timestamp = dt
            
        return await save_event(update, context, timestamp)
        
    except ValueError:
        await update.message.reply_text("⚠️ Formato non valido. Riprova (es: 14:30):")
        return INPUT_CUSTOM_TIME

async def save_event(update: Update, context: ContextTypes.DEFAULT_TYPE, timestamp: datetime.datetime):
    event_data = context.user_data.get('manual_event')
    if not event_data:
        msg = "Errore sessione persa."
        if update.callback_query: await update.callback_query.edit_message_text(msg)
        else: await update.message.reply_text(msg)
        return ConversationHandler.END
        
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if tenant:
            event_service = EventService(db)
            await event_service.add_event(
                tenant.id, 
                user_id, 
                event_data['type'], 
                event_data['details'],
                timestamp=timestamp
            )
            
    time_str = timestamp.strftime("%H:%M")
    succ_msg = f"✅ Evento salvato per le *{time_str}*!"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(succ_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(succ_msg, parse_mode='Markdown')
        
    return ConversationHandler.END

manual_log_handler = ConversationHandler(
    entry_points=[
        CommandHandler("log", manual_start),
        CallbackQueryHandler(manual_start, pattern='^start_manual_log$')
    ],
    states={
        SELECT_TYPE: [CallbackQueryHandler(select_type, pattern='^manual_type_|manual_cancel')],
        SELECT_TIME: [CallbackQueryHandler(select_time, pattern='^manual_time_|manual_cancel')],
        INPUT_CUSTOM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_time)]
    },
    fallbacks=[CommandHandler("cancel", manual_start)] # Should implement real cancel
)
