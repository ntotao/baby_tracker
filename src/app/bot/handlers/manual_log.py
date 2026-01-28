from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.event import EventService
from src.app.services.tenant import TenantService
import datetime
import logging

logger = logging.getLogger(__name__)

# States
SELECT_TYPE, SELECT_DURATION, SELECT_TIME, INPUT_CUSTOM_TIME, INPUT_VALUE, SELECT_START_TIME_INTERACTIVE = range(6)

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
        [InlineKeyboardButton("⚖️ Peso", callback_data='manual_type_weight'),
         InlineKeyboardButton("📏 Altezza", callback_data='manual_type_height')],
        [InlineKeyboardButton("❌ Annulla", callback_data='manual_menu_cancel')]
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
        await query.answer("Annullato.")
        from src.app.bot.handlers.tracking import menu_handler
        await menu_handler(update, context)
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
        
        # Special case for bottle: ask ML? No, user already did "Biberon manuale".
        # If manual_type_feed_bottle is clicked, it's treated as feed_bottle -> ask ML logic might be needed?
        # Actually in THIS handler we have manual_type_feed_bottle. 
        # Let's treat bottle as generic feed for now or handle ML if requested?
        # The user request specifically mentioned "Allattamenti manuali" (breast implies duration).
        # Bottle usually implies Quantity (ML).
        # Let's keep Start/Duration flow for Breast (Left/Right) and Bottle (maybe just time? or time+ml?).
        # User said "mia moglie segna orario inizio e durata". This implies breast. 
        # For bottle, we usually care about ML. 
        
        if source == 'bottle':
            # Redirect to bottle flow? Or just ask Time?
            # Existing 'Biberon' button in manual_start gives 'manual_type_feed_bottle'.
            # Let's handle generic Bottle here -> Ask ML -> Then Time.
            # But the request focuses on Start/Duration. 
            # Let's stick to Duration flow for Left/Right.
            pass

        details = {'source': source, 'manual': True}
        context.user_data['manual_event'] = {
            'type': event_type,
            'details': details
        }
        
        if source in ['left', 'right']:
             # NEW FLOW: Ask Start Time (Interactive) -> Then Duration
             
             # Init temp time (default to now, rounded to 5min)
             now = datetime.datetime.now()
             minute = now.minute - (now.minute % 5)
             start_time = now.replace(minute=minute, second=0, microsecond=0)
             
             context.user_data['temp_time'] = start_time
             context.user_data['temp_time_str'] = start_time.strftime("%H:%M")
             
             # Generate Keyboard
             msg_text, markup = generate_time_picker(start_time, source)
             
             await query.edit_message_text(msg_text, reply_markup=markup, parse_mode='Markdown')
             return SELECT_START_TIME_INTERACTIVE
             
        # For bottle we skip duration (usually) and just go to time... or do we want to ask ML here too?
        # Current manual_log doesn't support ML input yet. Let's send Bottle to TIME for now to avoid breaking scope.
        # Ideally we should ask ML for bottle in manual log too.
        
    elif event_type_raw == 'weight':
        event_type = 'misurazione_peso'
        context.user_data['manual_event'] = {'type': event_type, 'details': {}}
        await query.edit_message_text("⚖️ Inserisci il peso in **grammi** (es. 4500):", parse_mode='Markdown')
        return INPUT_VALUE

    elif event_type_raw == 'height':
        event_type = 'misurazione_altezza'
        context.user_data['manual_event'] = {'type': event_type, 'details': {}}
        await query.edit_message_text("📏 Inserisci l'altezza in **cm** (es. 55):", parse_mode='Markdown')
        return INPUT_VALUE

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

def generate_time_picker(dt: datetime.datetime, source: str):
    time_str = dt.strftime("%H:%M")
    date_str = "Oggi" if dt.date() == datetime.datetime.now().date() else dt.strftime("%d/%m")
    
    keyboard = [
        [InlineKeyboardButton("➕ 1h", callback_data='clk_h_inc'),
         InlineKeyboardButton("➕ 10m", callback_data='clk_m_inc')],
        
        [InlineKeyboardButton(f"🕒 {time_str}", callback_data='ignore'), # Display Key
         InlineKeyboardButton(f"📅 {date_str}", callback_data='clk_day_toggle')], 
        
        [InlineKeyboardButton("➖ 1h", callback_data='clk_h_dec'),
         InlineKeyboardButton("➖ 10m", callback_data='clk_m_dec')],
         
        [InlineKeyboardButton("✅ Conferma", callback_data='clk_confirm')],
        [InlineKeyboardButton("❌ Annulla", callback_data='manual_cancel')]
    ]
    
    text = f"🤱 *Allattamento {source.capitalize()}*\nSeleziona Orario Inizio:"
    return text, InlineKeyboardMarkup(keyboard)

async def handle_time_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'manual_cancel':
        await query.answer("Annullato.")
        from src.app.bot.handlers.tracking import menu_handler
        await menu_handler(update, context)
        return ConversationHandler.END

    # Ensure temp_time exists
    if 'temp_time' not in context.user_data:
        # Fallback if lost
        context.user_data['temp_time'] = datetime.datetime.now()
    
    current_time = context.user_data['temp_time']
    
    if data == 'clk_confirm':
        # Proceed to Duration
        context.user_data['manual_event_time'] = current_time # Save confirmed START time
        
        # Ask Duration
        keyboard = [
             [InlineKeyboardButton("5 min", callback_data='manual_dur_5'),
              InlineKeyboardButton("10 min", callback_data='manual_dur_10')],
             [InlineKeyboardButton("15 min", callback_data='manual_dur_15'),
              InlineKeyboardButton("20 min", callback_data='manual_dur_20')],
             [InlineKeyboardButton("30 min", callback_data='manual_dur_30'),
              InlineKeyboardButton("45 min", callback_data='manual_dur_45')],
             [InlineKeyboardButton("❌ Annulla", callback_data='manual_cancel')]
        ]
        await query.edit_message_text(
             f"✅ Inizio: *{current_time.strftime('%H:%M')}*\nQuanto è durato?",
             reply_markup=InlineKeyboardMarkup(keyboard),
             parse_mode='Markdown'
        )
        return SELECT_DURATION

    # Adjust Time
    if data == 'clk_h_inc': current_time += datetime.timedelta(hours=1)
    elif data == 'clk_h_dec': current_time -= datetime.timedelta(hours=1)
    elif data == 'clk_m_inc': current_time += datetime.timedelta(minutes=10)
    elif data == 'clk_m_dec': current_time -= datetime.timedelta(minutes=10)
    elif data == 'clk_day_toggle': 
        # Toggle Yesterday/Today
        if current_time.date() == datetime.datetime.now().date():
            current_time -= datetime.timedelta(days=1)
        else:
            current_time = current_time.replace(year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day)
    
    context.user_data['temp_time'] = current_time
    
    # Regenerate markup
    source = context.user_data['manual_event']['details']['source']
    msg_text, markup = generate_time_picker(current_time, source)
    
    try:
        await query.edit_message_text(msg_text, reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        logger.warning(f"Clock update skipped (content same?): {e}")
        
    await query.answer()
    return SELECT_START_TIME_INTERACTIVE

async def select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'manual_cancel':
        await query.answer("Annullato.")
        from src.app.bot.handlers.tracking import menu_handler
        await menu_handler(update, context)
        return ConversationHandler.END

    duration_min = int(data.replace('manual_dur_', ''))
    context.user_data['manual_event']['details']['duration_seconds'] = duration_min * 60
    context.user_data['manual_event']['details']['duration_text'] = f"{duration_min} min"

    # We already have start time from stored picker result
    start_time = context.user_data.get('manual_event_time')
    
    # Logic: The event needs a TIMESTAMP. The EventService uses timestamp as "Start Time" usually?
    # Actually add_event timestamp is "Event Time". For duration events, is it start or end?
    # Usually "Event occurred at X". For Feeding, X is Start Time usually.
    # Let's verify what we want. "Started at 14:00, lasted 15m". Event Timestamp = 14:00.
    
    return await save_event(update, context, start_time)

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'manual_cancel':
        await query.answer("Annullato.")
        from src.app.bot.handlers.tracking import menu_handler
        await menu_handler(update, context)
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

async def input_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value_text = update.message.text.strip()
    try:
        value = int(value_text)
        context.user_data['manual_event']['details']['value'] = value
        
        # Now ask for time
        keyboard = [
            [InlineKeyboardButton("Adesso", callback_data='manual_time_now')],
            [InlineKeyboardButton("-15 min", callback_data='manual_time_15'),
             InlineKeyboardButton("✍️ Data/Ora", callback_data='manual_time_custom')],
            [InlineKeyboardButton("❌ Annulla", callback_data='manual_cancel')]
        ]
        await update.message.reply_text(
            f"Valore registrato: {value}. Quando?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return SELECT_TIME
    except ValueError:
        await update.message.reply_text("⚠️ Inserisci un numero valido.")
        return INPUT_VALUE

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
        SELECT_TYPE: [CallbackQueryHandler(select_type, pattern='^manual_type_|manual_cancel|manual_menu_cancel')],
        SELECT_START_TIME_INTERACTIVE: [CallbackQueryHandler(handle_time_interaction, pattern='^clk_|manual_cancel')],
        SELECT_DURATION: [CallbackQueryHandler(select_duration, pattern='^manual_dur_|manual_cancel')],
        SELECT_TIME: [CallbackQueryHandler(select_time, pattern='^manual_time_|manual_cancel')],
        INPUT_CUSTOM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_time)],
        INPUT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_value)]
    },
    fallbacks=[CommandHandler("cancel", manual_start)] # Should implement real cancel
)
