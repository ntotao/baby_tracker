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
        [InlineKeyboardButton("🍼 Allattamento", callback_data='menu_feeding'),
         InlineKeyboardButton("💤 Nanna", callback_data='menu_sleep')],
        [InlineKeyboardButton("🩺 Salute", callback_data='menu_health'),
         InlineKeyboardButton("📝 Manuale", callback_data='start_manual_log')],
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
    
    logger.info(f"DEBUG: track_callback handling data={data} from user={user_id}")
    
    
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
            
        elif data == 'track_pipi':
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.answer("💧 Pipì registrata!", show_alert=False)
            
        elif data == 'track_entrambi':
            await event_service.add_event(tenant.id, user_id, 'cacca')
            await event_service.add_event(tenant.id, user_id, 'pipi')
            await query.answer("💩+💧 Entrambi registrati!", show_alert=False)

        # --- SUB MENUS ---
        # --- SUB MENUS ---
        elif data == 'menu_feeding':
            await query.answer()
            await show_feeding_menu(update)

        elif data == 'menu_sleep':
            await query.answer()
            await show_sleep_menu(update, context)

        elif data == 'menu_health':
            await query.answer()
            await show_health_menu(update)
            
        # --- SLEEP LOGIC ---
        elif data == 'sleep_start':
             context.user_data['sleep_start'] = datetime.datetime.now().timestamp()
             await show_sleep_active(update)
             await query.answer("💤 Buonanotte!")

        elif data == 'sleep_stop':
             if 'sleep_start' not in context.user_data:
                 await query.answer("Nessun sonno attivo.", show_alert=False)
                 await show_sleep_menu(update, context)
                 return
                 
             start_ts = context.user_data.pop('sleep_start')
             duration = int(datetime.datetime.now().timestamp() - start_ts)
             duration_min = duration // 60
             
             details = {
                 'duration_seconds': duration,
                 'duration_text': f"{duration_min} min"
             }
             await event_service.add_event(tenant.id, user_id, 'sonno', details)
             await query.answer(f"☀️ Buongiorno! Dormito {duration_min}m", show_alert=False)
             await menu_handler(update, context)

        # --- HEALTH LOGIC ---
        elif data.startswith('health_temp_'):
            val = data.replace('health_temp_', '')
            details = {'subtype': 'febbre', 'value': val}
            await event_service.add_event(tenant.id, user_id, 'salute', details)
            await query.answer(f"🌡️ Febbre {val}° registrata", show_alert=False)
            await menu_handler(update, context)

        elif data.startswith('health_med_'):
            med = data.replace('health_med_', '')
            details = {'subtype': 'medicina', 'note': med}
            await event_service.add_event(tenant.id, user_id, 'salute', details)
            await query.answer(f"💊 {med} registrata", show_alert=False)
            await menu_handler(update, context)
            
        elif data == 'health_vaccine':
            await event_service.add_event(tenant.id, user_id, 'salute', {'subtype': 'vaccino'})
            await query.answer("💉 Vaccino registrato", show_alert=False)
            await menu_handler(update, context)

        elif data.startswith('feed_timer_start_'):
             side = data.replace('feed_timer_start_', '')
             context.user_data['feeding_start'] = {
                 'side': side,
                 'start_time': datetime.datetime.now().timestamp()
             }
             await show_timer_active(update, side)
             await query.answer("⏱️ Timer avviato!")

        elif data == 'feed_timer_stop':
             if 'feeding_start' not in context.user_data:
                 await query.answer("Nessun timer attivo.", show_alert=False) # Changed
                 await menu_handler(update, context)
                 return
                 
             start_data = context.user_data.pop('feeding_start')
             duration = int(datetime.datetime.now().timestamp() - start_data['start_time'])
             duration_min = duration // 60
             
             details = {
                 'source': start_data['side'],
                 'duration_seconds': duration,
                 'duration_text': f"{duration_min} min"
             }
             
             await event_service.add_event(tenant.id, user_id, 'allattamento', details)
             await query.answer(f"✅ Poppata: {duration_min} min", show_alert=False) # Changed
             await menu_handler(update, context)

        elif data == 'feed_log_bottle':
             # Show ML options
             keyboard = [
                 [InlineKeyboardButton("20 ml", callback_data='feed_bottle_20'),
                  InlineKeyboardButton("30 ml", callback_data='feed_bottle_30')],
                 [InlineKeyboardButton("60 ml", callback_data='feed_bottle_60'),
                  InlineKeyboardButton("90 ml", callback_data='feed_bottle_90')],
                 [InlineKeyboardButton("120 ml", callback_data='feed_bottle_120')], 
                 [InlineKeyboardButton("🔙 Indietro", callback_data='menu_feeding')]
             ]
             await query.edit_message_text(
                 "🍼 *Biberon*\nQuanto latte?",
                 reply_markup=InlineKeyboardMarkup(keyboard),
                 parse_mode='Markdown'
             )

        elif data.startswith('feed_bottle_'):
             ml = data.replace('feed_bottle_', '')
             details = {'source': 'bottle', 'quantity_ml': ml}
             await event_service.add_event(tenant.id, user_id, 'allattamento', details)
             await query.answer(f"🍼 Biberon {ml}ml registrato!", show_alert=False)
             await menu_handler(update, context)

        elif data.startswith('feed_log_'):
            # Instant log (manual side without timer)
            feed_type = data.replace('feed_log_', '')
            details = {'source': feed_type}
            await event_service.add_event(tenant.id, user_id, 'allattamento', details)
            await query.answer(f"🍼 Allattamento ({feed_type}) registrato!", show_alert=False)
            await menu_handler(update, context)
            
        elif data == 'view_status':
            await query.answer()
            await show_status(update, tenant.id, event_service)

        elif data == 'delete_last_event':
            success = await event_service.delete_last_event(tenant.id)
            if success:
                 await query.answer("🗑️ Eliminato!", show_alert=False) # Changed
                 await show_status(update, tenant.id, event_service) # Refresh list
            else:
                 await query.answer("Nulla da eliminare.", show_alert=False) # Changed

        elif data == 'view_history':
             # Need to import locally to avoid circular import if history imports tracking
             from src.app.bot.handlers.history import history_list
             await history_list(update, context, 0)

        else:
            # Fallback for old buttons or unrecognized data
            await query.answer("🔄 Menu aggiornato.", show_alert=False) # Changed
            await menu_handler(update, context)

async def show_feeding_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("⏱️ Start Left 👈", callback_data='feed_timer_start_left'),
         InlineKeyboardButton("⏱️ Start Right 👉", callback_data='feed_timer_start_right')],
        [InlineKeyboardButton("📝 Log Biberon", callback_data='feed_log_bottle')],
        [InlineKeyboardButton("🔙 Indietro", callback_data='menu_main')]
    ]
    await update.callback_query.edit_message_text(
        "🍼 *Allattamento*\nScegli mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_timer_active(update: Update, side: str):
    side_icon = "👈" if side == 'left' else "👉"
    keyboard = [[InlineKeyboardButton("🛑 STOP Timer", callback_data='feed_timer_stop')]]
    await update.callback_query.edit_message_text(
        f"⏱️ *Allattamento in corso...* {side_icon}\nPremi Stop quando hai finito.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_status(update: Update, tenant_id: str, service: EventService):
    events = await service.get_recent_events(tenant_id, 10)
    summary = await service.get_daily_summary(tenant_id)
    
    last_feed = await service.get_last_event_by_type(tenant_id, 'allattamento')
    last_cacca = await service.get_last_event_by_type(tenant_id, 'cacca')
    last_pipi = await service.get_last_event_by_type(tenant_id, 'pipi')
    
    # --- SMART HEADER ---
    header_text = "📊 *Riepilogo Oggi:*\n"
    
    now = datetime.datetime.now()

    def format_diff(timestamp):
        diff = now - timestamp.replace(tzinfo=None)
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        if diff.days > 0: return ">24h"
        return f"{hours}h {minutes}m"

    # Feeding
    if last_feed:
        time_str = format_diff(last_feed.timestamp)
        last_side = last_feed.details.get('source', 'unknown') if last_feed.details else 'unknown'
        next_hint = "👉 Next: Right" if last_side == 'left' else "👈 Next: Left" if last_side == 'right' else ""
        header_text += f"🍼 *Poppata:* {time_str} fa ({last_side})\n   _{next_hint}_\n"
    else:
        header_text += "🍼 *Poppata:* --\n"

    # Cacca
    if last_cacca:
        header_text += f"💩 *Cacca:* {format_diff(last_cacca.timestamp)} fa\n"
    else:
        header_text += "💩 *Cacca:* --\n"

    # Pipi
    if last_pipi:
        header_text += f"💧 *Pipì:* {format_diff(last_pipi.timestamp)} fa\n"
    else:
        header_text += "💧 *Pipì:* --\n"
        
    header_text += "\n" # Spacer

    # Daily Counts
    if not summary:
        header_text += "_Nessun evento oggi._\n"
    else:
        counts = {s[0]: s[1] for s in summary}
        c_feed = counts.get('allattamento', 0)
        c_cacca = counts.get('cacca', 0)
        c_pipi = counts.get('pipi', 0)
        
        header_text += f"📆 *Oggi:* 🍼{c_feed} | 💩{c_cacca} | 💧{c_pipi}\n"
            
    # List
    events_text = "\n🕒 *Ultimi Eventi:*\n"
    for e in events:
        ts = e.timestamp.strftime("%H:%M")
        
        detail_str = ""
        if e.details and e.event_type == 'allattamento':
            src = e.details.get('source', '')
            dur = e.details.get('duration_text', '')
            if src == 'left': detail_str = f" (👈 {dur})"
            elif src == 'right': detail_str = f" (👉 {dur})"
            elif src == 'bottle':
                 ml = e.details.get('quantity_ml', '?')
                 detail_str = f" (🍼 {ml}ml)"
            else: detail_str = f" ({src})"
            
        icon = "⚪️"
        if e.event_type == 'cacca': icon = "💩"
        elif e.event_type == 'pipi': icon = "💧"
        elif e.event_type == 'allattamento': icon = "🍼"
        
        events_text += f"`{ts}` {icon} {e.event_type}{detail_str}\n"

    msg = f"{header_text}{events_text}"
    kb = [
        [InlineKeyboardButton("🔄 Aggiorna", callback_data='view_status')],
        [InlineKeyboardButton("📜 Storico Completo", callback_data='view_history')],
        [InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

async def show_sleep_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if sleep active
    if 'sleep_start' in context.user_data:
        await show_sleep_active(update)
        return

    keyboard = [
        [InlineKeyboardButton("💤 Inizia Nanna (Timer)", callback_data='sleep_start')],
        # Future: Manual Input
        [InlineKeyboardButton("🔙 Indietro", callback_data='menu_main')]
    ]
    await update.callback_query.edit_message_text(
        "🌙 *Nanna*\nAvvia il timer quando si addormenta:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_sleep_active(update: Update):
    keyboard = [[InlineKeyboardButton("☀️ SVEGLIA (Stop)", callback_data='sleep_stop')]]
    await update.callback_query.edit_message_text(
        "💤 *Zzz...*\nBimbo che dorme... Premi Stop al risveglio.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_health_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("🌡️ 37.5°", callback_data='health_temp_37.5'),
         InlineKeyboardButton("🌡️ 38°", callback_data='health_temp_38'),
         InlineKeyboardButton("🌡️ 38.5°", callback_data='health_temp_38.5')],
        [InlineKeyboardButton("🌡️ 39°", callback_data='health_temp_39'),
         InlineKeyboardButton("🌡️ 39.5°", callback_data='health_temp_39.5'),
         InlineKeyboardButton("🌡️ 40°", callback_data='health_temp_40')],
        [InlineKeyboardButton("💊 Tachipirina", callback_data='health_med_tachipirina'),
         InlineKeyboardButton("💊 Vitamina D", callback_data='health_med_vitd')],
        [InlineKeyboardButton("💉 Vaccino", callback_data='health_vaccine')],
        [InlineKeyboardButton("🔙 Indietro", callback_data='menu_main')]
    ]
    await update.callback_query.edit_message_text(
        "🩺 *Salute*\nCosa vuoi registrare?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler(update, context)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await update.message.reply_text("Non hai un tracker attivo.")
            return
        event_service = EventService(db)
        await show_status(update, tenant.id, event_service)

# Handler Exports
menu_cmd_handler = CommandHandler("menu", menu_handler)
status_cmd_handler = CommandHandler("status", status_command)
# Catch-all for track_, feed_, view_status
track_handler = CallbackQueryHandler(track_callback, pattern="^(track_|feed_|view_|menu_|delete_|sleep_|health_)") 
back_handler = CallbackQueryHandler(back_to_menu, pattern="^menu_main$")
