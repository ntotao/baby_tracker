# Baby Tracker - Telegram Bot & Home Assistant Integration

**Baby Tracker** è un sistema self-hosted per tracciare la crescita e le attività del neonato direttamente da **Telegram**, utilizzando **Home Assistant** come database e cervello centrale.

![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?style=for-the-badge&logo=home-assistant)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED?style=for-the-badge&logo=docker)

## ✨ Funzionalità

*   **Pannolini**: Registra cambio pannolino (Pipì / Cacca / Mista) con un solo tap.
*   **Allattamento**:
    *   Timer in tempo reale (Start/Stop).
    *   Supporto per allattamento al seno (Destra/Sinistra/Entrambi) o Biberon.
    *   Inserimento manuale retroattivo.
*   **Crescita**: Monitoraggio di Peso, Altezza e Circonferenza Cranica.
*   **Statistiche**: Riepilogo giornaliero richiamabile in chat.
*   **Integrazione HA**: Tutte le registrazioni diventano entità in Home Assistant (`input_datetime`, `counter`, ecc.), ideali per creare dashboard storiche con Grafana o Lovelace.

## 🚀 Quick Start

Hai già familiarità con Docker e Home Assistant? Ecco come partire subito.

1.  **Home Assistant**: Copia la cartella `ha_package` dentro la tua cartella `config/packages/` di HA e riavvia HA.
2.  **Preparazione**:
    *   Ottieni un **Long-Lived Access Token** dal tuo profilo Home Assistant.
    *   Crea un bot con **@BotFather** su Telegram e ottieni il Token.
3.  **Configurazione**:
    *   Rinomina `bot/.env.example` in `bot/.env`.
    *   Inserisci i token e l'URL del tuo HA nel file `.env`.
4.  **Avvio**:
    ```bash
    docker-compose up -d --build
    ```
5.  **Utilizzo**: Cerca il tuo bot su Telegram e invia `/start`.

---

## 🛠️ Guida all'Installazione

### 1. Configurazione Home Assistant
Il bot necessita di specifici "Helpers" in Home Assistant per memorizzare i dati.

1.  Assicurati che il tuo `configuration.yaml` includa la gestione dei packages:
    ```yaml
    homeassistant:
      packages: !include_dir_named packages
    ```
2.  Copia il file `ha_package/baby_tracker.yaml` (o l'intera cartella) dentro `config/packages/` del tuo Home Assistant.
3.  **Riavvia Home Assistant** per caricare le nuove entità.

### 2. Creazione Token HA
Per permettere al bot di scrivere dati su HA:
1.  Vai sul tuo **Profilo Utente** in Home Assistant (clicca sulle iniziali in basso a sinistra).
2.  Scorri fino a "Token di accesso a lunga durata".
3.  Clicca su **Crea Token**, dagli un nome (es. "BabyTracker") e copia la stringa generata.

### 3. Configurazione Bot
1.  Clona questo repository.
2.  Entra nella cartella `bot`:
    ```bash
    cd bot
    cp .env.example .env
    ```
3.  Modifica il file `.env` con un editor di testo:
    ```ini
    HA_URL=http://tuo-ind-ip-homeassistant:8123
    HA_TOKEN=il_tuo_token_lunga_durata_qui
    TELEGRAM_TOKEN=il_tuo_telegram_bot_token
    ```

### 4. Avvio con Docker
Dalla cartella principale del progetto (dove si trova `docker-compose.yml`):

```bash
docker-compose up -d --build
```
Il bot verrà compilato e avviato in pochi istanti.

## 📱 Comandi Telegram

*   `/start` - Avvia il bot e mostra il menu principale.
*   `/menu` - Mostra la tastiera con le opzioni rapide.
*   `/help` - Mostra l'elenco dei comandi e istruzioni.

## 📂 Struttura Cartelle

*   `bot/` - Codice sorgente Python del bot.
*   `ha_package/` - Configurazione YAML per Home Assistant (Sensori, Input, ecc.).
*   `docker-compose.yml` - Orchestrazione del container Docker.
