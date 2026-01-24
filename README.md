# 👶 Baby Tracker - The "Parenting Survival" Home Assistant Integration

**Trasforma il caos in dati!** Perché cercare di ricordare a che ora è stata l'ultima poppata quando puoi chiederlo a un bot?

**Baby Tracker** è l'integrazione per **Home Assistant** che ti permette di loggare pannolini, poppate e crescita direttamente da **Telegram**. Perché ammettiamolo, hai il telefono in mano anche alle 3 di notte mentre cull il pupo.

![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Sleep](https://img.shields.io/badge/Sleep-Optional-red.svg)
![Coffee](https://img.shields.io/badge/Coffee-Required-brown.svg)
![Diapers](https://img.shields.io/badge/Diapers-Infinite-yellow.svg)

## 🎭 Perché ti serve?

*   🤯 **Memoria da Pesce Rosso**: "Amore, a che ora ha mangiato?" -> "Boh." -> *Panico*. Con Baby Tracker apri Telegram e sai.
*   📊 **Grafici per Nerd**: Vuoi correlare la durata della poppata con la probabilità di un pannolino esplosivo? Ora puoi (con Grafana).
*   👪 **Teamwork**: Mamma e Papà usano lo stesso bot. Niente più foglietti di carta persi o app non sincronizzate.

## ✨ Cosa sa fare (oltre a non dormire)

*   💩 **Pannolini**: Registra le "produzioni artistiche" (Pipì / Cacca / Disastro Nucleare) con un tap.
*   🍼 **Allattamento**:
    *   **Timer Live**: Premi Start quando inizi, Stop quando crolli (tu o lui/lei).
    *   **Manuale**: "Ah già, ha mangiato un'ora fa".
    *   **Lati**: Dx, Sx, Entrambi o Biberon.
*   📏 **Crescita**: Peso, Altezza e "Testone" (Circonferenza).

## 🚀 Installazione (HACS)

Ok, bando alle ciance. Ecco come si mette in piedi la baracca.

### 1. Inietta gli Helper (YAML)
Dobbiamo dire ad Home Assistant dove mettere i dati (perché il database SQL non ci piace nudo e crudo).

1.  Prendi il file `ha_package/baby_tracker.yaml` e buttalo con cattiveria nella cartella `config/packages/` del tuo Home Assistant.
    *   *Nota da Nerd*: Controlla di avere `packages: !include_dir_named packages` nel tuo `configuration.yaml` se no non va nulla.
2.  **Riavvia HA**. Incrocia le dita.

### 2. HACS Attack
1.  Apri HACS.
2.  Menu (tre puntini) -> "Repository Personalizzati".
3.  Incolla il link del tuo repo: `https://github.com/TUO_USERNAME/baby_tracker`.
4.  Categoria: "Integration".
5.  Installa. Riavvia. Solita roba.

### 3. Configurazione Finale
1.  **Impostazioni** -> **Dispositivi e Servizi** -> **Aggiungi Integrazione**.
2.  Cerca **Baby Tracker**.
3.  Dagli in pasto il **Telegram Bot Token** (chiama @BotFather se non ce l'hai).
4.  Fine. Scrivi `/start` al bot e goditi il monitoraggio.

---

*Fatto con ❤️ (e poco sonno) da un genitore per genitori.*
