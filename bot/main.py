import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
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

from ha_client import HomeAssistantClient

# Load env variables
load_dotenv()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize HA Client
ha = HomeAssistantClient(HA_URL, HA_TOKEN)

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

# ------------------------------------------------------------------------------
# HANDLERS
# ------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu."""
    if update.message:
        await update.message.reply_text('👶 Baby Tracker Bot - Main Menu:', reply_markup=main_menu_keyboard())
    else:
        # If triggered by a "Cancel" or "Back" callback that calls start()
        query = update.callback_query
        await query.answer()
        await query.edit_message_text('👶 Baby Tracker Bot - Main Menu:', reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles main menu buttons (Diaper, Status) that don't start a conversation."""
    query = update.callback_query
    data = query.data

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    if data.startswith('diaper_'):
        await handle_diaper(update, context)
        return ConversationHandler.END
    
    if data == 'start_feeding_flow':
        # Check if timer is running
        state_obj = ha.get_state(ENTITIES['feeding_active'])
        is_active = state_obj and state_obj.get('state') == 'on'
        
        if is_active:
            # Timer is running -> Show Stop Menu
            keyboard = [[InlineKeyboardButton("⏹️ STOP Poppata", callback_data='live_stop')]]
            await query.edit_message_text("⏱️ Poppata in corso... Terminare?", reply_markup=InlineKeyboardMarkup(keyboard))
            return LIVE_STOP_SIDE # Next step is choosing side after stop
        else:
            # Timer not running -> Show Start/Manual Menu
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
        # Show Growth Sub-menu
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
    await query.answer()

    if data == 'diaper_poo':
        ha.increment_counter(ENTITIES['poo_counter'])
        ha.update_date_time_now(ENTITIES['poo_time'])
        await query.edit_message_text("✅ Registrata Cacca!", reply_markup=back_button())
    
    elif data == 'diaper_pee':
        ha.increment_counter(ENTITIES['pee_counter'])
        ha.update_date_time_now(ENTITIES['pee_time'])
        await query.edit_message_text("✅ Registrata Pipì!", reply_markup=back_button())

    elif data == 'diaper_both':
        ha.increment_counter(ENTITIES['poo_counter'])
        ha.update_date_time_now(ENTITIES['poo_time'])
        ha.increment_counter(ENTITIES['pee_counter'])
        ha.update_date_time_now(ENTITIES['pee_time'])
        await query.edit_message_text("✅ Registrato Cambio Completo!", reply_markup=back_button())

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    poo_count = ha.get_state(ENTITIES['poo_counter']) or {'state': '?'}
    pee_count = ha.get_state(ENTITIES['pee_counter']) or {'state': '?'}
    feed_count = ha.get_state(ENTITIES['feeding_counter']) or {'state': '?'}
    
    text = (
        f"📊 **Stato Giornaliero**\n\n"
        f"💩 Cacche: {poo_count['state']}\n"
        f"💧 Pipì: {pee_count['state']}\n"
        f"🍼 Poppate: {feed_count['state']}"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=back_button())

# ------------------------------------------------------------------------------
# FEEDING FLOW HANDLERS
# ------------------------------------------------------------------------------

async def feeding_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'live_start':
        # Start Timer
        ha.call_service('input_boolean', 'turn_on', {'entity_id': ENTITIES['feeding_active']})
        ha.update_date_time_now(ENTITIES['feeding_start'])
        
        keyboard = [[InlineKeyboardButton("⏹️ STOP Poppata", callback_data='live_stop')]]
        await query.edit_message_text("▶️ Poppata AVVIATA! Premi Stop quando finito.", reply_markup=InlineKeyboardMarkup(keyboard))
        return LIVE_STOP_SIDE # In this state we wait for stop

    elif data == 'manual_entry':
        # Ask Time
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

async def live_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when user presses STOP on a live timer."""
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'live_stop':
        # Stop Timer Logic
        ha.call_service('input_boolean', 'turn_off', {'entity_id': ENTITIES['feeding_active']})
        ha.update_date_time_now(ENTITIES['feeding_end'])
        
        # Ask Side
        keyboard = [
            [InlineKeyboardButton("Sinistra (SX)", callback_data='side_sx'),
             InlineKeyboardButton("Destra (DX)", callback_data='side_dx')],
            [InlineKeyboardButton("Entrambi", callback_data='side_both'),
             InlineKeyboardButton("Biberon", callback_data='side_bottle')]
        ]
        await query.edit_message_text("Poppata terminata! Quale lato?", reply_markup=InlineKeyboardMarkup(keyboard))
        return LIVE_STOP_SIDE # Re-using this state to capture side choice

    # If it's a side choice coming from the just-stopped timer
    if data.startswith('side_'):
        side = data.replace('side_', '')
        ha.call_service('input_text', 'set_value', {'entity_id': ENTITIES['feeding_side'], 'value': side})
        ha.increment_counter(ENTITIES['feeding_counter'])
        
        # Calculate duration for feedback (optional, HA has timestamps)
        await query.edit_message_text("✅ Poppata registrata!", reply_markup=back_button())
        return ConversationHandler.END

async def manual_time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    # Calculate timestamps based on selection
    now = datetime.now()
    start_dt = now
    
    if data == 'time_15':
        start_dt = now - timedelta(minutes=15)
    elif data == 'time_30':
        start_dt = now - timedelta(minutes=30)
    elif data == 'time_60':
        start_dt = now - timedelta(hours=1)
    
    context.user_data['manual_start'] = start_dt

    # Ask Duration
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

    # Ask Side
    keyboard = [
        [InlineKeyboardButton("Sinistra (SX)", callback_data='side_sx'),
         InlineKeyboardButton("Destra (DX)", callback_data='side_dx')],
        [InlineKeyboardButton("Entrambi", callback_data='side_both'),
         InlineKeyboardButton("Biberon", callback_data='side_bottle')]
    ]
    await query.edit_message_text("Quale lato?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MANUAL_SIDE

async def manual_side_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    side = data.replace('side_', '')
    start_dt = context.user_data['manual_start']
    end_dt = context.user_data['manual_end']
    duration_str = f"{context.user_data['manual_duration']} min"

    # Save everything to HA
    ha.update_date_time_custom(ENTITIES['feeding_start'], start_dt)
    ha.update_date_time_custom(ENTITIES['feeding_end'], end_dt)
    
    ha.call_service('input_text', 'set_value', {'entity_id': ENTITIES['feeding_side'], 'value': side})
    ha.call_service('input_text', 'set_value', {'entity_id': ENTITIES['feeding_duration'], 'value': duration_str})
    
    ha.increment_counter(ENTITIES['feeding_counter'])

    await query.edit_message_text("✅ Poppata manuale registrata con successo!", reply_markup=back_button())
    return ConversationHandler.END

# ------------------------------------------------------------------------------
# GROWTH FLOW HANDLERS
# ------------------------------------------------------------------------------

async def growth_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'main_menu':
        await start(update, context)
        return ConversationHandler.END

    # Mapping button data to entity key and unit
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

async def growth_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text input for growth values."""
    text = update.message.text.replace(',', '.') # Handle comma decimals
    growth_type = context.user_data.get('growth_type')

    try:
        value = float(text)
    except ValueError:
        await update.message.reply_text("⛔ Per favore inserisci un numero valido (es. 3.5). Riprova:")
        return GROWTH_INPUT

    # Save to HA
    entity_map = {
        'growth_weight': ENTITIES['weight'],
        'growth_height': ENTITIES['height'],
        'growth_head': ENTITIES['head']
    }
    
    if growth_type in entity_map:
        ha.set_value(entity_map[growth_type], value)
        ha.update_date_time_now(ENTITIES['growth_time'])
        
        await update.message.reply_text(f"✅ Valore registrato: {value}", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Errore interno.", reply_markup=main_menu_keyboard())

    return ConversationHandler.END

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment variables.")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Conversation Handler for Feeding
    feeding_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback, pattern='^start_feeding_flow$')],
        states={
            FEEDING_MENU_STATE: [
                CallbackQueryHandler(feeding_menu_choice, pattern='^(live_start|manual_entry|main_menu)$')
            ],
            LIVE_STOP_SIDE: [
                CallbackQueryHandler(live_stop_handler, pattern='^(live_stop|side_.*)$')
            ],
            MANUAL_TIME: [
                CallbackQueryHandler(manual_time_choice, pattern='^(time_.*|main_menu)$')
            ],
            MANUAL_DURATION: [
                CallbackQueryHandler(manual_duration_choice, pattern='^(dur_.*|main_menu)$')
            ],
            MANUAL_SIDE: [
                CallbackQueryHandler(manual_side_choice, pattern='^side_.*$')
            ],
        },
        fallbacks=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^main_menu$')]
    )

    # Conversation Handler for Growth
    growth_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_callback, pattern='^growth_menu$')],
        states={
            GROWTH_MENU: [
                CallbackQueryHandler(growth_menu_choice, pattern='^(growth_.*|main_menu)$')
            ],
            GROWTH_INPUT: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), growth_input_handler),
                CallbackQueryHandler(start, pattern='^main_menu$')
            ]
        },
        fallbacks=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^main_menu$')]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(feeding_conv)
    application.add_handler(growth_conv)
    application.add_handler(CallbackQueryHandler(main_menu_callback)) # Fallback for non-conv buttons

    print("Bot is running...")
    application.run_polling()
