from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService
from src.app.db.models import Baby
from sqlalchemy import select
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# States
SET_NAME, SET_DOB = range(2)

async def child_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        
        if not tenant:
            await update.message.reply_text("Non hai un tracker attivo.")
            return ConversationHandler.END
            
        # Check existing baby
        stmt = select(Baby).where(Baby.tenant_id == tenant.id)
        result = await db.execute(stmt)
        baby = result.scalar_one_or_none()
        
        context.user_data['tenant_id'] = tenant.id
        
        if baby:
            msg = f"👶 *Profilo Baby*\n\nNome: {baby.name}\n"
            if baby.birth_date:
                msg += f"Data Nascita: {baby.birth_date.strftime('%d/%m/%Y')}\n"
            
            msg += "\nVuoi modificare i dati? Scrivi il *Nuovo Nome* (o /cancel per uscire)."
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "👶 *Benvenuto!*\nConfiguriamo il profilo del tuo bimbo/a.\n\nCome si chiama?",
                parse_mode='Markdown'
            )
            
        return SET_NAME

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 2 or len(name) > 30:
        await update.message.reply_text("⚠️ Il nome deve essere tra 2 e 30 caratteri. Riprova:")
        return SET_NAME
        
    context.user_data['baby_name'] = name
    
    await update.message.reply_text(
        f"Piacere, {name}! 💕\n\nOra dimmi la data di nascita (formato GG/MM/AAAA):"
    )
    return SET_DOB

async def set_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dob_text = update.message.text
    try:
        dob = datetime.strptime(dob_text, "%d/%m/%Y")
        
        tenant_id = context.user_data['tenant_id']
        name = context.user_data['baby_name']
        
        async with AsyncSessionLocal() as db:
            # Check/Update Baby
            stmt = select(Baby).where(Baby.tenant_id == tenant_id)
            result = await db.execute(stmt)
            baby = result.scalar_one_or_none()
            
            if not baby:
                baby = Baby(tenant_id=tenant_id, name=name, birth_date=dob)
                db.add(baby)
            else:
                baby.name = name
                baby.birth_date = dob
                
            await db.commit()
            
        await update.message.reply_text(f"✅ Profilo di *{name}* salvato!", parse_mode='Markdown')
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("⚠️ Formato non valido. Usa GG/MM/AAAA (es. 15/05/2026). Riprova:")
        return SET_DOB

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operazione annullata.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

profile_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("child", child_start)],
    states={
        SET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
        SET_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_dob)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
