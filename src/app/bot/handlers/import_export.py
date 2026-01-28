from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService
from src.app.services.event import EventService
import datetime
import csv
import io
import logging

logger = logging.getLogger(__name__)

# States
WAITING_FILE = 0

async def import_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await update.message.reply_text("Non hai un tracker attivo.")
            return ConversationHandler.END
            
    await update.message.reply_text(
        "📂 *Importazione Dati*\n\n"
        "Invia un file **CSV** con questo formato (punto e virgola `;` come separatore):\n\n"
        "`DD/MM/YYYY;HH:MM;TIPO;VALORE;NOTE`\n\n"
        "Esempi:\n"
        "`28/01/2026;14:30;cacca;;`\n"
        "`28/01/2026;15:00;allattamento;left;15m` (durata)\n"
        "`28/01/2026;18:00;biberon;120ml;` (quantità)\n"
        "`28/01/2026;09:00;peso;4550;` (grammi)\n\n"
        "Invia /cancel per annullare.",
        parse_mode='Markdown'
    )
    return WAITING_FILE

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    # Check mime type or extension? Telegram often sends generic types.
    # filename check is safer for user intention.
    if not document.file_name.lower().endswith('.csv') and not document.file_name.lower().endswith('.txt'):
        await update.message.reply_text("⚠️ Per favore invia un file .csv o .txt.")
        return WAITING_FILE

    file = await document.get_file()
    content_byte = await file.download_as_bytearray()
    content_str = content_byte.decode('utf-8')
    
    # Process CSV
    imported_count = 0
    errors = []
    
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        event_service = EventService(db)
        
        # Determine dialect? assume semicolon
        f = io.StringIO(content_str)
        reader = csv.reader(f, delimiter=';')
        
        row_num = 0
        for row in reader:
            row_num += 1
            if not row: continue
            
            # Skip header if present
            if row[0].lower().startswith('date') or row[0].lower().startswith('data'):
                continue
                
            try:
                # Expected: Date;Time;Type;Val1;Val2
                # Allow flexible len
                if len(row) < 3:
                    errors.append(f"Riga {row_num}: Dati insufficienti")
                    continue
                    
                date_str = row[0].strip()
                time_str = row[1].strip()
                type_str = row[2].strip().lower()
                val1 = row[3].strip().lower() if len(row) > 3 else ""
                val2 = row[4].strip() if len(row) > 4 else "" # unused for now
                
                # Parse DateTime
                dt_str = f"{date_str} {time_str}"
                # Try format %d/%m/%Y %H:%M
                try:
                    timestamp = datetime.datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    # Try %Y-%m-%d
                    timestamp = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                
                # Normalize Type
                event_type = None
                details = {'source': 'import'}
                
                if 'cacca' in type_str: event_type = 'cacca'
                elif 'pipi' in type_str or 'pipì' in type_str: event_type = 'pipi'
                
                elif 'allattamento' in type_str or 'feed' in type_str:
                    event_type = 'allattamento'
                    if 'left' in val1 or 'sx' in val1: details['source'] = 'left'
                    elif 'right' in val1 or 'dx' in val1: details['source'] = 'right'
                    
                    if 'm' in val1: # duration e.g. 15m
                         try:
                             mins = int(val1.replace('m','').strip())
                             details['duration_text'] = f"{mins} min"
                             details['duration_seconds'] = mins * 60
                         except: pass
                         
                elif 'biberon' in type_str or 'bottle' in type_str:
                    event_type = 'allattamento'
                    details['source'] = 'bottle'
                    if 'ml' in val1:
                        details['quantity_ml'] = val1.replace('ml','').strip()
                    else:
                        details['quantity_ml'] = val1 # assume raw number
                        
                elif 'peso' in type_str or 'weight' in type_str:
                    event_type = 'misurazione_peso'
                    try: details['value'] = int(val1)
                    except: pass
                    
                elif 'altezza' in type_str or 'height' in type_str:
                    event_type = 'misurazione_altezza'
                    try: details['value'] = int(val1)
                    except: pass
                
                if event_type:
                    await event_service.add_event(tenant.id, user_id, event_type, details, timestamp)
                    imported_count += 1
                else:
                    errors.append(f"Riga {row_num}: Tipo '{type_str}' ignoto")

            except Exception as e:
                errors.append(f"Riga {row_num}: Errore {str(e)}")
                
    msg = f"✅ Importazione completata!\n\n📥 **Importati:** {imported_count}\n"
    if errors:
        msg += f"⚠️ **Errori ({len(errors)}):**\n" + "\n".join(errors[:5])
        if len(errors) > 5: msg += f"\n...e altri {len(errors)-5}"
        
    await update.message.reply_text(msg, parse_mode='Markdown')
    return ConversationHandler.END

async def import_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Importazione annullata.")
    return ConversationHandler.END

import_handler = ConversationHandler(
    entry_points=[CommandHandler("import", import_start)],
    states={
        WAITING_FILE: [MessageHandler(filters.Document.ALL, process_file)]
    },
    fallbacks=[CommandHandler("cancel", import_cancel)]
)
