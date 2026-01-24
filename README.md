# Baby Tracker - Home Assistant Integration

**Baby Tracker** è un'integrazione personalizzata (Custom Component) per **Home Assistant** che trasforma **Telegram** in un'interfaccia per tracciare la crescita e le attività del neonato.

![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?style=for-the-badge&logo=home-assistant)

## ✨ Funzionalità

*   **Pannolini**: Registra cambio pannolino (Pipì / Cacca / Mista) con un solo tap.
*   **Allattamento**: Timer Live, Inserimento Manuale, gestione lati (Dx/Sx/Biberon).
*   **Crescita**: Monitoraggio Peso, Altezza, Circonferenza.
*   **Statistiche**: Riepilogo giornaliero in chat.
*   **Nativo**: Gira direttamente dentro Home Assistant, nessuna configurazione Docker complessa.

## 🚀 Installazione (HACS)

### 1. Preparazione Entità
Attualmente l'integrazione si appoggia ad alcuni Helper standard (`input_datetime`, `counter`, ecc.).

1.  Copia il file `ha_package/baby_tracker.yaml` nella tua cartella `config/packages/` di Home Assistant.
    *   *Nota*: Assicurati di avere `packages: !include_dir_named packages` nel tuo `configuration.yaml`.
2.  Riavvia Home Assistant per creare le entità.

### 2. Installazione Componente
1.  Apri HACS in Home Assistant.
2.  Vai su "Integrazioni" -> Menu (tre puntini) -> "Repository Personalizzati".
3.  Incolla l'URL di questo repository: `https://github.com/TUO_USERNAME/baby_tracker`.
4.  Categoria: "Integration".
5.  Clicca su **Installa**.
6.  Riavvia Home Assistant.

### 3. Configurazione
1.  Vai su **Impostazioni** -> **Dispositivi e Servizi**.
2.  Clicca su **Aggiungi Integrazione**.
3.  Cerca **Baby Tracker**.
4.  Inserisci il tuo **Telegram Bot Token** (ottienilo da @BotFather).
5.  Fatto! Invia `/start` al tuo bot su Telegram.

## 📂 Struttura Cartelle

*   `custom_components/baby_tracker/`: Il cuore dell'integrazione.
*   `ha_package/`: Configurazione YAML degli helper.
