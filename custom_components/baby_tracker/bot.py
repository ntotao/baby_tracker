"""Telegram Bot Logic for Baby Tracker."""
import logging
from functools import wraps
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Entity Constant Map
ENTITIES = {
    'poo_time': 'input_datetime.baby_last_poo',
    'pee_time': 'input_datetime.baby_last_pee',
    'poo_counter': 'counter.baby_diaper_poo_daily',
    'pee_counter': 'counter.baby_diaper_pee_daily',
    # Feeding
    'feeding_start': 'input_datetime.baby_last_feeding_start',
    'feeding_end': 'input_datetime.baby_last_feeding_end',
    'feeding_active': 'input_boolean.baby_feeding_timer_active',
    'feeding_side': 'input_text.baby_last_feeding_side',
    'feeding_duration': 'input_text.baby_last_feeding_duration',
    'feeding_counter': 'counter.baby_feeding_daily',
    # Growth
    'weight': 'input_number.baby_weight',
    'height': 'input_number.baby_height',
    'head': 'input_number.baby_head_circumference',
    'growth_time': 'input_datetime.baby_last_growth'
}

# Conversation States
(
    FEEDING_MENU_STATE,
    MANUAL_TIME,
    MANUAL_DURATION,
    MANUAL_SIDE,
    LIVE_STOP_SIDE,
    GROWTH_MENU,
    GROWTH_INPUT
) = range(7)

def get_hass(context: ContextTypes.DEFAULT_TYPE) -> HomeAssistant:
    """Retrieve hass instance from bot_data."""
    return context.bot_data.get('hass')

def check_access(func):
    """Decorator to check if user has access."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        allowed_ids = context.bot_data.get('allowed_ids', [])
        user_id = update.effective_user.id
        
        # If no IDs are configured, allow everyone (or deny? Safe default: allow but log warning)
        # Decision: If empty, we could warn, but for security, usually Allow List implies Deny All Else.
        # User explicitly asked for multi-user config.
        
        if allowed_ids and user_id not in allowed_ids:
            _LOGGER.warning("Unauthorized access attempt from User ID: %s", user_id)
            if update.message:
                await update.message.reply_text(f"⛔ **Access Denied**\nYour ID: `{user_id}`\n\nAsk the owner to add this ID to Home Assistant Baby Tracker configuration.", parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.answer("⛔ Access Denied", show_alert=True)
            return ConversationHandler.END
            
        return await func(update, context, *args, **kwargs)
    return wrapper

# ------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------
def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu Principale", callback_data='main_menu')]])

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💩 E' Cacca", callback_data='diaper_poo'),
         InlineKeyboardButton("💧 E' Pipì", callback_data='diaper_pee')],
        [InlineKeyboardButton("💩 + 💧 Entrambi", callback_data='diaper_both')],
        [InlineKeyboardButton("🍼 Allattamento", callback_data='start_feeding_flow')],
        [InlineKeyboardButton("📏 Crescita", callback_data='growth_menu')],
        [InlineKeyboardButton("📊 Stato", callback_data='status')]
    ])

async def update_timestamp(hass: HomeAssistant, entity_id: str, dt: datetime = None):
    """Update an input_datetime to now or specific time."""
    if dt is None:
        dt = datetime.now()
    
    await hass.services.async_call(
        'input_datetime', 
        'set_datetime', 
        {'entity_id': entity_id, 'timestamp': dt.timestamp()}
    )

# ------------------------------------------------------------------------------
# HANDLERS
# ------------------------------------------------------------------------------

@check_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu."""
    if update.message:
        await update.message.reply_text('👶 Baby Tracker Bot - Main Menu:', reply_markup=main_menu_keyboard())
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text('👶 Baby Tracker Bot - Main Menu:', reply_markup=main_menu_keyboard())
    return ConversationHandler.END

@check_access
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    hass = get_hass(context)

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    if data.startswith('diaper_'):
        await handle_diaper(update, context)
        return ConversationHandler.END
    
    if data == 'start_feeding_flow':
        state = hass.states.get(ENTITIES['feeding_active'])
        is_active = state and state.state == 'on'
        
        if is_active:
            keyboard = [[InlineKeyboardButton("⏹️ STOP Poppata", callback_data='live_stop')]]
            await query.edit_message_text("⏱️ Poppata in corso... Terminare?", reply_markup=InlineKeyboardMarkup(keyboard))
            return LIVE_STOP_SIDE 
        else:
            keyboard = [
                [InlineKeyboardButton("▶️ AVVIA Timer", callback_data='live_start')],
                [InlineKeyboardButton("📝 Inserimento Manuale", callback_data='manual_entry')],
                [InlineKeyboardButton("🔙 Annulla", callback_data='main_menu')]
            ]
            await query.edit_message_text("Allattamento:", reply_markup=InlineKeyboardMarkup(keyboard))
            return FEEDING_MENU_STATE

    if data == 'status':
        await show_status(update, context)
        return ConversationHandler.END
        
    if data == 'growth_menu':
        keyboard = [
            [InlineKeyboardButton("⚖️ Peso", callback_data='growth_weight')],
            [InlineKeyboardButton("📏 Altezza", callback_data='growth_height')],
            [InlineKeyboardButton("🧠 Circonferenza", callback_data='growth_head')],
            [InlineKeyboardButton("🔙 Annulla", callback_data='main_menu')]
        ]
        await query.edit_message_text("Cosa vuoi registrare?", reply_markup=InlineKeyboardMarkup(keyboard))
        return GROWTH_MENU

async def handle_diaper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    hass = get_hass(context)
    await query.answer()

    if data == 'diaper_poo':
        await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['poo_counter']})
        await update_timestamp(hass, ENTITIES['poo_time'])
        await query.edit_message_text("✅ Registrata Cacca!", reply_markup=back_button())
    
    elif data == 'diaper_pee':
        await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['pee_counter']})
        await update_timestamp(hass, ENTITIES['pee_time'])
        await query.edit_message_text("✅ Registrata Pipì!", reply_markup=back_button())

    elif data == 'diaper_both':
        await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['poo_counter']})
        await update_timestamp(hass, ENTITIES['poo_time'])
        await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['pee_counter']})
        await update_timestamp(hass, ENTITIES['pee_time'])
        await query.edit_message_text("✅ Registrato Cambio Completo!", reply_markup=back_button())

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    hass = get_hass(context)
    
    def get_state(entity_id):
        s = hass.states.get(entity_id)
        return s.state if s else '?'

    poo = get_state(ENTITIES['poo_counter'])
    pee = get_state(ENTITIES['pee_counter'])
    feed = get_state(ENTITIES['feeding_counter'])
    
    text = (
        f"📊 **Stato Giornaliero**\n\n"
        f"💩 Cacche: {poo}\n"
        f"💧 Pipì: {pee}\n"
        f"🍼 Poppate: {feed}"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=back_button())

# ------------------------------------------------------------------------------
# FEEDING FLOW
# ------------------------------------------------------------------------------
@check_access
async def feeding_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    hass = get_hass(context)
    await query.answer()

    if data == 'live_start':
        await hass.services.async_call('input_boolean', 'turn_on', {'entity_id': ENTITIES['feeding_active']})
        await update_timestamp(hass, ENTITIES['feeding_start'])
        
        keyboard = [[InlineKeyboardButton("⏹️ STOP Poppata", callback_data='live_stop')]]
        await query.edit_message_text("▶️ Poppata AVVIATA! Premi Stop quando finito.", reply_markup=InlineKeyboardMarkup(keyboard))
        return LIVE_STOP_SIDE 

    elif data == 'manual_entry':
        keyboard = [
            [InlineKeyboardButton("Adesso", callback_data='time_now')],
            [InlineKeyboardButton("15 min fa", callback_data='time_15')],
            [InlineKeyboardButton("30 min fa", callback_data='time_30')],
            [InlineKeyboardButton("1 ora fa", callback_data='time_60')],
            [InlineKeyboardButton("🔙 Annulla", callback_data='main_menu')]
        ]
        await query.edit_message_text("Quando è iniziata la poppata?", reply_markup=InlineKeyboardMarkup(keyboard))
        return MANUAL_TIME

    elif data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

@check_access
async def live_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    hass = get_hass(context)
    await query.answer()

    if data == 'live_stop':
        await hass.services.async_call('input_boolean', 'turn_off', {'entity_id': ENTITIES['feeding_active']})
        await update_timestamp(hass, ENTITIES['feeding_end'])
        
        keyboard = [
            [InlineKeyboardButton("Sinistra (SX)", callback_data='side_sx'),
             InlineKeyboardButton("Destra (DX)", callback_data='side_dx')],
            [InlineKeyboardButton("Entrambi", callback_data='side_both'),
             InlineKeyboardButton("Biberon", callback_data='side_bottle')]
        ]
        await query.edit_message_text("Poppata terminata! Quale lato?", reply_markup=InlineKeyboardMarkup(keyboard))
        return LIVE_STOP_SIDE

    if data.startswith('side_'):
        side = data.replace('side_', '')
        await hass.services.async_call('input_text', 'set_value', {'entity_id': ENTITIES['feeding_side'], 'value': side})
        await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['feeding_counter']})
        
        await query.edit_message_text("✅ Poppata registrata!", reply_markup=back_button())
        return ConversationHandler.END

@check_access
async def manual_time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    now = datetime.now()
    start_dt = now
    
    if data == 'time_15':
        start_dt = now - timedelta(minutes=15)
    elif data == 'time_30':
        start_dt = now - timedelta(minutes=30)
    elif data == 'time_60':
        start_dt = now - timedelta(hours=1)
    
    context.user_data['manual_start'] = start_dt

    keyboard = [
        [InlineKeyboardButton("5 min", callback_data='dur_5'),
         InlineKeyboardButton("10 min", callback_data='dur_10')],
        [InlineKeyboardButton("15 min", callback_data='dur_15'),
         InlineKeyboardButton("20 min", callback_data='dur_20')],
        [InlineKeyboardButton("30 min", callback_data='dur_30'),
         InlineKeyboardButton("45 min", callback_data='dur_45')],
        [InlineKeyboardButton("🔙 Annulla", callback_data='main_menu')]
    ]
    await query.edit_message_text("Quanto è durata?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANUAL_DURATION

@check_access
async def manual_duration_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    duration_min = int(data.replace('dur_', ''))
    start_dt = context.user_data.get('manual_start', datetime.now())
    end_dt = start_dt + timedelta(minutes=duration_min)
    
    context.user_data['manual_end'] = end_dt
    context.user_data['manual_duration'] = duration_min

    keyboard = [
        [InlineKeyboardButton("Sinistra (SX)", callback_data='side_sx'),
         InlineKeyboardButton("Destra (DX)", callback_data='side_dx')],
        [InlineKeyboardButton("Entrambi", callback_data='side_both'),
         InlineKeyboardButton("Biberon", callback_data='side_bottle')]
    ]
    await query.edit_message_text("Quale lato?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANUAL_SIDE

@check_access
async def manual_side_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    hass = get_hass(context)
    await query.answer()

    side = data.replace('side_', '')
    start_dt = context.user_data['manual_start']
    end_dt = context.user_data['manual_end']
    duration_str = f"{context.user_data['manual_duration']} min"

    await update_timestamp(hass, ENTITIES['feeding_start'], start_dt)
    await update_timestamp(hass, ENTITIES['feeding_end'], end_dt)
    
    await hass.services.async_call('input_text', 'set_value', {'entity_id': ENTITIES['feeding_side'], 'value': side})
    await hass.services.async_call('input_text', 'set_value', {'entity_id': ENTITIES['feeding_duration'], 'value': duration_str})
    
    await hass.services.async_call('counter', 'increment', {'entity_id': ENTITIES['feeding_counter']})

    await query.edit_message_text("✅ Poppata manuale registrata con successo!", reply_markup=back_button())
    return ConversationHandler.END

# ------------------------------------------------------------------------------
# GROWTH FLOW
# ------------------------------------------------------------------------------
@check_access
async def growth_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    context.user_data['growth_type'] = data
    
    if data == 'growth_weight':
        msg = "Inserisci il PESO in Kg (es. 3.5):"
    elif data == 'growth_height':
        msg = "Inserisci l'ALTEZZA in cm (es. 60.5):"
    elif data == 'growth_head':
        msg = "Inserisci la CIRCONFERENZA in cm (es. 40):"
    else:
        await start(update, context)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("🔙 Annulla", callback_data='main_menu')]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    return GROWTH_INPUT

@check_access
async def growth_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(',', '.')
    growth_type = context.user_data.get('growth_type')
    hass = get_hass(context)

    try:
        value = float(text)
    except ValueError:
        await update.message.reply_text("⛔ Per favore inserisci un numero valido (es. 3.5). Riprova:")
        return GROWTH_INPUT

    entity_map = {
        'growth_weight': ENTITIES['weight'],
        'growth_height': ENTITIES['height'],
        'growth_head': ENTITIES['head']
    }
    
    if growth_type in entity_map:
        await hass.services.async_call('input_number', 'set_value', {'entity_id': entity_map[growth_type], 'value': value})
        await update_timestamp(hass, ENTITIES['growth_time'])
        
        await update.message.reply_text(f"✅ Valore registrato: {value}", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Errore interno.", reply_markup=main_menu_keyboard())

    return ConversationHandler.END


async def setup_bot(hass: HomeAssistant, token: str, allowed_ids: list):
    """Initialize and start the bot."""
    application = ApplicationBuilder().token(token).build()
    
    # Inject hass context AND allowed IDs
    application.bot_data['hass'] = hass
    application.bot_data['allowed_ids'] = allowed_ids
    
    feeding_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback, pattern='^start_feeding_flow$')],
        states={
            FEEDING_MENU_STATE: [CallbackQueryHandler(feeding_menu_choice, pattern='^(live_start|manual_entry|main_menu)$')],
            LIVE_STOP_SIDE: [CallbackQueryHandler(live_stop_handler, pattern='^(live_stop|side_.*)$')],
            MANUAL_TIME: [CallbackQueryHandler(manual_time_choice, pattern='^(time_.*|main_menu)$')],
            MANUAL_DURATION: [CallbackQueryHandler(manual_duration_choice, pattern='^(dur_.*|main_menu)$')],
            MANUAL_SIDE: [CallbackQueryHandler(manual_side_choice, pattern='^side_.*$')],
        },
        fallbacks=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^main_menu$')]
    )

    growth_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback, pattern='^growth_menu$')],
        states={
            GROWTH_MENU: [CallbackQueryHandler(growth_menu_choice, pattern='^(growth_.*|main_menu)$')],
            GROWTH_INPUT: [MessageHandler(filters.TEXT & (~filters.COMMAND), growth_input_handler), CallbackQueryHandler(start, pattern='^main_menu$')]
        },
        fallbacks=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^main_menu$')]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(feeding_conv)
    application.add_handler(growth_conv)
    application.add_handler(CallbackQueryHandler(main_menu_callback))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    return application
