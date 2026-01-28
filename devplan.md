# Piano Tecnico Evoluto: Baby Tracker Standalone

Ciao! Ho rivisto il piano con un occhio da "Staff Engineer". Il piano originale era buono, ma per renderlo davvero solido, manutenibile e scalabile (e "vendibile" anche come codice open-source di qualità), ho apportato upgrade significativi allo stack e all'architettura.

## 🚀 Visione Architetturale "Senior"
Passiamo da un semplice script a un'architettura a servizi.
- **Framework**: `FastAPI` (web server) + `python-telegram-bot` (PTB) v21+ (Async). Perché? FastAPI gestisce webhook Stripe e Healthchecks in modo nativo e performante (ASGI). PTB gira nel lifecycle di FastAPI.
- **Database**: `SQLAlchemy 2.0` (Async) + `Aiosqlite` (Dev) / `AsyncPG` (Prod) + `Alembic` (Migrations). Perché? Raw SQL è fragile. L'ORM ci dà sicurezza e le migrazioni (Alembic) sono vitali per evolvere lo schema senza perdere dati utenti.
- **Dependency Management**: `uv` (o `poetry`). Molto più veloce e deterministico di `pip` + `requirements.txt`.
- **Quality Assurance**: `ruff` (linter/formatter velocissimo), `mypy` (typing stretto), `pre-commit` hooks.

---

## 📅 Roadmap Dettagliata

### Milestone 1: The "Solid Foundation" (3-5 Giorni)
*Obiettivo: Setup ambiente professionale, DB layer robusto e Bot che risponde "Pong".*

#### 1.1 Tooling & Repository
- **Tool**: Usa `uv` per gestire il progetto.
- **Struttura**: "Package-based" structure.
  ```text
  baby_tracker/
  ├── src/
  │   ├── app/
  │   │   ├── api/          # Endpoints FastAPI (Stripe, HA hook)
  │   │   ├── bot/          # PTB Handlers & Logic
  │   │   ├── core/         # Config, Security, Logging
  │   │   ├── db/           # SQLAlchemy models & session
  │   │   └── services/     # Business Logic (disaccoppiata dal bot)
  │   └── main.py           # Entry point
  ├── alembic/              # DB Migrations
  ├── tests/
  ├── docker-compose.yml
  └── pyproject.toml        # Deps definition
  ```

#### 1.2 Database (Async + ORM)
- Setup `SQLAlchemy` async engine.
- Definizione Modelli (`Tenant`, `Event`, `User`).
- **Multi-tenancy**: Implementare a livello di Service. Ogni query filtra per `tenant_id`.

#### 1.3 Bot + Web Server Integration
- Pattern consigliato: `Application.builder().updater(None)...`
- FastAPI `lifespan` gestisce start/stop del bot e setup dei webhook.

---

### Milestone 2: Core Domain & UX (5-7 Giorni)
*Obiettivo: Il tracker funziona perfettamente per un utente singolo e gruppi.*

#### 2.1 Services Layer
- Implementare `EventService`: metodi come `add_event`, `get_daily_summary`.
- Questo layer è indipendente da Telegram! Facilita i test e future API REST.

#### 2.2 Telegram Interface
- **Menu Dinamici**: Tastiere inline che cambiano stato.
- **Input Wizards**: ConversationHandler per input complessi (es. quantità latte, note).
- **"Stato" View**: Renderizzazione Markdown pulita delle ultime N ore.

#### 2.3 Scheduler
- Usare `APScheduler` (integrato in PTB o standalone su FastAPI) per i reminder (es. "Sono passate 3 ore dall'ultima poppata").

---

### Milestone 3: Monetization & Pro Features (4-6 Giorni)
*Obiettivo: Rendere il progetto sostenibile.*

#### 3.1 Stripe Integration
- Endpoint FastAPI `/webhook/stripe`.
- Logica: Quando arriva `checkout.session.completed`, aggiorna field `is_premium` del Tenant.
- **Premium Gating**: Decoratore python `@require_premium` sui service methods o handlers.

#### 3.2 Advanced Analytics
- Generazione grafici con `matplotlib` (o `plotly` to image) in thread pool (per non bloccare async loop).
- Export CSV/PDF.

#### 3.3 Privacy & GDPR
- Comandi `/delete_my_data`, `/export_data`.

---

### Milestone 4: Production Readiness (2-3 Giorni)
*Obiettivo: Deploy "Fire and Forget".*

#### 4.1 Docker
- Multi-stage build per immagine leggera (<200MB).
- Healthcheck endpoint `/health`.

#### 4.2 CI/CD
- GitHub Actions: Run `ruff`, `mypy`, `pytest` su ogni push.
- Build & Push Docker image su release.

---

### Milestone 5: Home Assistant Integration (Future)
*Obiettivo: L'ecosistema si chiude.*
- Il bot espone API (protette da API Key) che HA può chiamare.
- Oppure il bot può chiamare webhook di HA quando registra un evento.
- Decoupling totale: Il bot è la "Source of Truth", HA è un consumer.

---

## 🛠️ Tech Stack Upgrade Summary
| Componente | Piano Originale | Piano "Staff Engineer" | Vantaggi |
|------------|-----------------|------------------------|----------|
| **Lang** | Python 3.x | Python 3.12+ | Typing, Perf |
| **Deps** | pip | `uv` / `poetry` | Speed, Lockfile, Security |
| **Web** | Flask (Threaded) | **FastAPI** (ASGI) | Async nativo, Doc auto (Swagger) |
| **Bot** | PTB Sync/Async | **PTB v21** (Full Async) | Performance, Concurrency |
| **DB** | Raw SQL + Pysqlcipher | **SQLAlchemy** + **Alembic** | Maintainability, Migrations, Agnostic |
| **Linting**| - | `ruff` + `mypy` | Code Quality, Bug Prevention |

Che ne pensi? Se approvi, partiamo con la **Milestone 1**: Pulizia e Setup Architetturale.