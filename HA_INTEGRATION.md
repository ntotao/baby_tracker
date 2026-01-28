# 🏠 Home Assistant Integration Guide

Questa guida ti spiega come integrare **Baby Tracker Bot** con **Home Assistant (HA)** per visualizzare i dati del tuo bambino direttamente nella dashboard domotica.

## 🛠️ Come Funziona

L'integrazione non usa MQTT o API esterne complesse. Il Bot espone una **API HTTP locale** che Home Assistant interroga (polling) per leggere lo stato.
Inoltre, il Bot può ricevere eventi da HA tramite chiamate API, permettendoti di creare pulsanti fisici (es. ZigBee) per registrare eventi.

---

## 📂 Installazione del Custom Component

1.  **Trova la cartella**:
    Vai nella root del tuo progetto Baby Tracker scaricato: `custom_components/baby_tracker`.

2.  **Copia in Home Assistant**:
    Devi copiare l'intera cartella `baby_tracker` dentro la cartella `custom_components` della tua installazione di Home Assistant via File Editor o Samba.
    
    Il percorso finale deve essere:
    `/config/custom_components/baby_tracker/`

3.  **Verifica i file**:
    Assicurati che dentro ci siano `manifest.json`, `__init__.py` e `sensor.py`.

---

## ⚙️ Configurazione YAML

Aggiungi il sensore al tuo `configuration.yaml` di Home Assistant.

```yaml
sensor:
  - platform: baby_tracker
    host: http://192.168.1.100:8000  # L'IP dove gira il BOT e la porta (default 8000)
    telegram_id: 123456789           # Il TUO ID Telegram (User ID)
    name: "Alessandro"               # (Opzionale) Nome del bambino/tracker
```

*   **host**: Se usi Docker sullo stesso server di HA, potresti usare l'IP locale della macchina. Se usi HA OS e il bot è un addon (futuro), sarà diverso. Per ora metti l'IP della macchina dove hai lanciato `docker compose`.
*   **telegram_id**: Per trovarlo, scrivi qualsiasi messaggio al bot e guarda i log, oppure chiedilo a @userinfobot su Telegram.

### Riavvio
Riavvia Home Assistant per caricare il componente.

---

## 📊 Entità Disponibili

Una volta riavviato, avrai a disposizione questi sensori:

*   `sensor.alessandro_ultime_poppata` (Timestamp)
*   `sensor.alessandro_lato_poppata` (left/right)
*   `sensor.alessandro_ultima_cacca` (Timestamp)
*   `sensor.alessandro_ultima_pipi` (Timestamp)
*   `sensor.alessandro_poppate_oggi` (Numero)
*   `sensor.alessandro_cacche_oggi` (Numero)
*   `sensor.alessandro_pipi_oggi` (Numero)

---

## 🎛️ Esempi Lovelace (Dashboard)

Ecco come creare una bella card per vedere lo stato.

### Esempio Base due Entità
```yaml
type: entities
title: Baby Status
entities:
  - entity: sensor.alessandro_ultime_poppata
    format: relative  # Mostra "2 hours ago"
  - entity: sensor.alessandro_lato_poppata
  - entity: sensor.alessandro_poppate_oggi
```

### Pulsanti di Azione (Avanzato)
Puoi usare `rest_command` in HA per creare pulsanti che inviano dati al bot.

In `configuration.yaml`:
```yaml
rest_command:
  baby_log_cacca:
    url: "http://192.168.1.100:8000/api/ha/event"
    method: POST
    content_type: "application/json"
    payload: '{"telegram_id": 123456789, "event_type": "cacca"}'
```

Poi nella dashboard usi un pulsante che chiama il servizio `rest_command.baby_log_cacca`.

---

## ❓ Troubleshooting

*   **Stato "Unavailable"?** Controlla che il bot sia acceso e che l'IP sia corretto. Prova ad aprire `http://IP:8000/health` nel browser.
*   **Non trovo i sensori?** Controlla i log di Home Assistant (`Settings -> System -> Logs`) per errori relativi a `baby_tracker`.
