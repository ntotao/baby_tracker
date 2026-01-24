# 🤖 Configurazione BotFather

Questa guida ti spiega come creare e configurare al meglio il tuo bot su Telegram per renderlo più carino e facile da usare.

## 1. Crea il Bot
1.  Su Telegram cerca **@BotFather**.
2.  Scrivi `/newbot`.
3.  Scegli un **Nome** (es. "Leo Tracker"). Questo è quello che vedrai nella chat.
4.  Scegli uno **Username** (deve finire con `bot`, es. `leo_tracker_bot`).
5.  Copia il **Token** che ti viene dato. Questo va nella configurazione di Home Assistant.

## 2. Aggiungi i Comandi al Menu
Per avere il tasto "Menu" (quello blu in basso a sinistra) sempre disponibile:

1.  Scrivi `/setcommands` a BotFather.
2.  Seleziona il tuo bot.
3.  Incolla questa lista:
    ```text
    start - 🚀 Avvia il Bot / Menu Principale
    menu - 📱 Mostra la tastiera comandi
    status - 📊 Statistiche di oggi
    help - ℹ️ Guida ai comandi
    ```

## 3. Personalizza l'Aspetto
Rendiamolo più amichevole!

*   **Immagine Profilo**:
    1.  Scrivi `/setuserpic`.
    2.  Invia una foto carina (magari un'icona di un biberon o una foto stilizzata).
*   **Descrizione** (Cosa fa il bot):
    1.  Scrivi `/setdescription`.
    2.  Es: "Il bot per tracciare la crescita di Leo! 🍼"
*   **About** (Info profilo):
    1.  Scrivi `/setabouttext`.
    2.  Es: "Powered by Home Assistant Baby Tracker."

## 4. Disabilita i Gruppi (Opzionale)
Se userai il bot solo tu e il tuo partner in chat privata (consigliato per la privacy):

1.  Scrivi `/setjoingroups`.
2.  Seleziona "Disable".
    *   *Nota*: Se invece vuoi usarlo in un gruppo comune con mamma/papà, lascialo su Enable!

---
**Fatto!** Ora il tuo bot è pronto e configurato professionalmente.
