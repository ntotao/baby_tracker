from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from src.app.db.session import AsyncSessionLocal
from src.app.services.tenant import TenantService
from src.app.services.event import EventService
from src.app.services.charts import ChartService
from src.app.db.models import Event
from sqlalchemy import select, and_

async def growth_chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    msg = await update.message.reply_text("⏳ Generazione grafico in corso...")
    
    async with AsyncSessionLocal() as db:
        tenant_service = TenantService(db)
        tenant = await tenant_service.get_tenant_by_user(user_id)
        if not tenant:
            await msg.edit_text("Nessun tracker attivo.")
            return

        # Fetch weights
        stmt_w = select(Event).where(
            and_(Event.tenant_id == tenant.id, Event.event_type == 'misurazione_peso')
        ).order_by(Event.timestamp)
        result_w = await db.execute(stmt_w)
        events_w = result_w.scalars().all()
        
        # Fetch heights
        stmt_h = select(Event).where(
            and_(Event.tenant_id == tenant.id, Event.event_type == 'misurazione_altezza')
        ).order_by(Event.timestamp)
        result_h = await db.execute(stmt_h)
        events_h = result_h.scalars().all()
        
    if not events_w and not events_h:
        await msg.edit_text("📉 Nessun dato di crescita registrato.")
        return

    # Prepare data for service
    # Service expects list of (datetime, value)
    data_w = []
    for e in events_w:
        val = e.details.get('value')
        if val: data_w.append((e.timestamp, val))
        
    data_h = []
    for e in events_h:
        val = e.details.get('value')
        if val: data_h.append((e.timestamp, val))
        
    # Generate Chart
    try:
        buf = ChartService.create_growth_chart(data_w, data_h)
        
        await msg.delete() # Remove "generating..." 
        await update.message.reply_photo(photo=buf, caption="📈 *Grafico di Crescita*", parse_mode='Markdown')
        
    except Exception as e:
        await msg.edit_text(f"❌ Errore generazione grafico: {e}")

chart_handler = CommandHandler("growth", growth_chart_command)
