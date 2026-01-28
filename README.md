# 👶 Baby Tracker Bot

Un bot Telegram **self-hosted** per tracciare la vita del neonato, pensato per genitori geek che vogliono privacy, dati e condivisione in tempo reale.

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Database](https://img.shields.io/badge/DB-PostgreSQL%2FSQLite-blue)

## ✨ Funzionalità

### 🍼 Allattamento & Pappa
*   **Timer Live**: Start/Stop per Tetta Destra/Sinistra.
*   **Log Manuale "Smart"**: Inserisci durata e orario di inizio con un orologio interattivo (stile Apple) o backdata eventi passati.
*   **Biberon**: Registra quantità esatte (ml).
*   **Status View**: Vedi subito quanto tempo è passato dall'ultima poppata e quale lato tocca adesso ("Next Side").

### 💩 Cambio Pannolino
*   Registro rapido per **Cacca** e **Pipì** (o entrambi).
*   Ultimo cambio sempre visibile nello stato.

### 📉 Crescita
*   Registro **Peso** e **Altezza**.
*   (Coming soon) Grafici di crescita.

### 👪 Multi-Utente & Condivisione
*   **Tenant System**: Ogni tracker è un "gruppo" isolato.
*   **Invite Link**: Genera un link `/invite` dal pannello Admin per aggiungere partner/nonni al tuo stesso tracker. Tutti vedono e aggiornano gli stessi dati.

### 🛠️ Utility Pro
*   **Storico Interattivo (`/history`)**: Scorri gli ultimi eventi, e cancellali chirurgicamente se hai sbagliato.
*   **Bulk Import (`/import`)**: Carica vecchi dati da Excel/CSV per non perdere nulla.
*   **Profilo Baby (`/child`)**: Gestisci Nome e Data di nascita.

---

## 🚀 Installazione (Docker)

Il modo più veloce per partire.

1.  **Clona il repo**:
    ```bash
    git clone https://github.com/ntotao/baby_tracker.git
    cd baby_tracker
    ```

2.  **Configura Env**:
    Crea un file `.env` copiando l'esempio:
    ```bash
    TELEGRAM_TOKEN=tuo_token_botfather
    DATABASE_URL=sqlite+aiosqlite:///./baby_tracker.db
    ```

3.  **Avvia**:
    ```bash
    docker compose up -d --build
    ```

4.  **Usa**:
    Apri il bot su Telegram e premi `/start`.

---

## 📂 Struttura Progetto

*   `src/app/bot`: Logica del Bot Telegram (Handlers, Menu).
*   `src/app/db`: Modelli SQLAlchemy e gestione sessione.
*   `src/app/services`: Logica di business (EventService, TenantService).
*   `migrations/`: Aggiornamenti database (Alembic).

## 🤖 Comandi Bot

Vedi [bot_config.md](bot_config.md) per la lista completa da dare a @BotFather.

---
*Fatto con ❤️ (e poco sonno).*
