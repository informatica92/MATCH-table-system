# MATCH-table-system
 This Streamlit app allows users to manage and join board game reservations. 
 Users can create new game table propositions, view available tables, and join them by specifying their username. 
 The app also fetches and displays the game's main image from BoardGameGeek using the game's BGG ID.

https://github.com/user-attachments/assets/74ca4b9c-25d9-4934-8c9f-a3f02dbdc303

# 🇮🇹 Italian
## Come iniziare
L'applicazione è live su https://match-table-system.streamlit.app/ utilizzando https://streamlit.io/cloud per un hosting gratuito.

In caso si voglia invece eseguire l'applicazione in locale è necessario seguire i passi sotto indicati: 
0. Installare Python (con Anaconda)
 - https://docs.anaconda.com/anaconda/install/windows/
1. Clone del repository
  ```
  git clone https://github.com/informatica92/MATCH-table-system.git
  ```
3. Creazione e attivazione di un virtualenv
 ```
 python -m venv venv
 source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
 ```
5. Installazione delle dipendenza
 ```
 pip install -r requirements.txt
 ```
7. Eseguire
 ```
 streamlit run board_game_manager.py
 ```
## Funzionalità
### Inserimento username
1. Se non è visibile, espandere la sidebar sulla sinistra,
2. inserire un username nella casella di testo apposita e premere INVIO.
3. L'applicazione ora vi identificherà con quell'username e vi abiliterà le opzioni di: 
   - creazione di una proposta (o tavolo) 
   - unione ad una proposta (o tavolo)
### Creazione di una proposta/tavolo (richiede inserimento username)
1. Passare alla tab dedicata (la seconda) e inserire il titolo del gioco nella prima casella di testo. Premere INVIO.
2. La selezione sottostante acquisirà ora i titoli di BGG che corrispondono al titolo inserito sopra (così come la ricerca su BGG)
3. Scegliete ora un titolo da quella selezione per automatizzare la ricerca dell'immagine, della descrizione, delle meccaniche e delle categorie
4. Inserire:
   - il numero di giocatori,
   - la durata prevista
   - data e ora
   - note
5. Premere "Create Proposition" per salvare
6. Il tavolo proposto sarà ora visibile nella tab apposita (la prima)
### Visualizzazione proposte/tavoli
1. Accedere alla tab apposita (la prima)
2. Scorrere tra le proposte (in ordine di creazione)
### Unione ad una proposta/tavolo (richiede inserimento username)
1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Join Table X"

NB: 
- Puoi accedere solo una volta ad ogni tavolo con uno specifico username
- Se invece del bottone viene mostrato un messaggio "Set a username to join a table", espandere la sidebar e impostare l'username come indicato sopra
### Rimozione di un utente da un tavolo 
1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Leave" in corrispndenza dell'utente che si desidera rimuovere
### Rimozione di una proposta
1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Delete proposition" 

NB: 
 - Per ragioni di sicurezza, possono essere rimossi solo i tavoli vuoti
### (OPZIONALE) Invio notifica su un canale Telegram dedicato
Valorizzando le variabili d'ambiente 
 - TELEGRAM_CHAT_ID
 - TELEGRAM_BOT_TOKEN
Una notifica sul rispettivo canale (chat id/channel id) verrà inviata automaticamente: 
 - al momento della creazione di un tavolo
### (OPZIONALE) Data precompilata
Valorizzando le variabili d'ambiente
 - DEFAULT_DATE
il selettore della data nella tab di creazione verrà inizializzato a quel valore.

ATTENZIONE: il formato deve essere YYYY-MM-DD, es: 2024-09-29


# English
