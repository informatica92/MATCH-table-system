# MATCH-table-system
 This Streamlit app allows users to manage and join board game reservations. 
 Users can create new game table propositions, view available tables, and join them by specifying their username. 
 The app also fetches and displays the game's main image from BoardGameGeek using the game's BGG ID.

https://github.com/user-attachments/assets/74ca4b9c-25d9-4934-8c9f-a3f02dbdc303

# 🇮🇹 Italian
## Come iniziare
L'applicazione è live su https://match-table-system.streamlit.app/ utilizzando https://streamlit.io/cloud per un hosting gratuito.

In caso si voglia invece eseguire l'applicazione in locale è necessario seguire i passi sotto indicati: 

1. Installare Python
- con [Anaconda](https://docs.anaconda.com/anaconda/install/windows/)
- tramite [sito ufficiale](https://www.python.org/downloads/)
2. Clone del repository
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
6. Creazione di un file `secrets.toml` con le seguenti variabili d'ambiente (oppure valorizza i secrets durante il deploy su Streamlit Cloud):

| Section               | Variabile d'ambiente  | Descrizione                                                                                                                                             | Default              | Obbligatorio |
|-----------------------|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|--------------|  
| # POSTGRESQL DATABASE | DB_HOST               | Hostname del database                                                                                                                                   | localhost            | No           |
|                       | DB_NAME               | Nome del database                                                                                                                                       |                      | Sì           |
|                       | DB_USER               | Username del database                                                                                                                                   |                      | Sì           | 
|                       | DB_PASSWORD           | Password del database                                                                                                                                   |                      | Sì           |
|                       | DB_PORT               | Porta del database                                                                                                                                      | 5432                 | No           |
|                       | DB_SCHEMA             | Schema del database (pre esistente)                                                                                                                     | public               | No           |
| # TELEGRAM            | TELEGRAM_CHAT_ID      | Chat ID di Telegram a cui inviare messaggi                                                                                                              |                      | No           |
|                       | TELEGRAM_BOT_TOKEN    | Token del bot di Telegram, se mancante, non viene effettuato alcun invio                                                                                |                      | No           |
| # MAP                 | GMAP_MAP_URL          | URL della mappa di Google Maps, se mancante non viene mostrata alcuna mappa                                                                             |                      | No           |
| # GENERAL SETTINGS    | TITLE                 | Titolo dell'applicazione                                                                                                                                | Board Game Proposals | No           |
|                       | LOGO                  | URL del logo dell'applicazione                                                                                                                          |                      | Sì           |
|                       | LOGO_LARGE            | URL del logo grande dell'applicazione, se mancante viene usato come logo della sidebar il logo in LOGO                                                  |                      | No           |
|                       | DEFAULT_DATE          | Data predefinita per la creazione di un tavolo nel formato `YYYY-MM-DD`, se mancante o nel passato, viene usata la data odierna                         | *data odierna*       | No           |
|                       | GOD_MODE_PASSWORD     | Password per attivare la GOD MODE, se mancante, la God Mode non è attivabile                                                                            |                      | Sì           |
| [auth]                | redirect_uri          | URI di reindirizzamento per l'autenticazione, può essere: <br/> - http://localhost:8501/oauth2callback <br/> - https://`dominio deploy`/oauth2callback  |                      | Sì           |
|                       | cookie_secret         | Nome del cookie in cui inserire il token di autenticazione                                                                                              |                      | Sì           |
| [auth.auth0]          | client_id             | Client ID di Auth0                                                                                                                                      |                      | Sì           |
|                       | client_secret         | Client Secret di Auth0                                                                                                                                  |                      | Sì           |
|                       | server_metadata_url   | URL del server metadata di Auth0, nella forma https://`dominio auth0`.com/.well-known/openid-configuration                                              |                      | Sì           |

7. Eseguire
 ```
 streamlit run board_game_manager.py
 ```
## Funzionalità

### 🎉 Novità: Gestione delle Espansioni
E' ora possibile aggiungere espansioni ai giochi, in modo da poter specificare quali espansioni saranno utilizzate durante la partita.
E' anche possibile modificare le espansioni in seguito utilizzando il tasto "Edit" disponibile sotto ogni proposta.

### 🎉 Novità: Le Tabs sono ora Pages
Quelle che precedentemente erano tabs ora sono state trasformate in pagine, per una navigazione più fluida e intuitiva

Seleziona una pagina dal menu a sinistra per accedere alle funzionalità desiderate

### 🎉 Novità: Login(?)

### 🎉 Novità: Nuova pagina "User"
E' ora possibile accedere ad una pagina interamente dedicata all'utente in cui è possibile impostare campi come:
 - nome
 - cognome
 - username
 - Telegram username
 - BGG username

### 🎉 Novità: Funzionalità "Locations"
A parte le location di sistema, ogni utente può ora aggiungere una o più location in cui è disponibile a giocare.

L'utilizzo delle location sarà introdotto successivamente, per ora è possibile solo aggiungerle e visualizzarle 

### Delete ora con finestra di conferma e permette eliminazione di tavoli con 1+ giocatori
<p><img src="https://github.com/user-attachments/assets/b3589ef2-7869-43fa-9f53-94d2d6562e5a" alt="join toast" height="400"/></p>

Delete ha ora una finestra di conferma e permette anche l'eliminazione di tavoli con 1+ giocatori

### Leave/Delete/Edit possibili solo per sè stessi e per i propri tavoli
<p><img src="https://github.com/user-attachments/assets/53569a54-15a5-4961-b48d-a4fef435f709" alt="join toast" height="400"/></p>

Leave/Delete/Edit possibili solo per sè stessi e per i propri tavoli: 
 - Leave è quindi abilitata solo per sè stessi e per i giocatori ai propri tavoli
 - Delete/Edit è quindi possibile solo per i propri tavoli 

### GOD MODE introdotta per rendere Leave/Delete/Edit possibili sempre
<p><img src="https://github.com/user-attachments/assets/2c133444-8b32-46a0-bc41-ae115bf36d71" alt="join toast" height="400"/></p>

La GOD MODE permette, in caso si disponga di una password, di superare il vincolo per cui Leave/Delete/Edit è possibile solo per sè stessi e per i propri tavoli 

### Vista a Tabella
<p><img src="https://github.com/user-attachments/assets/9d5dd314-2af6-4d2d-9114-5d3464e9d993" alt="join toast" height="400"/></p>

E' stata aggiunta una visualizzazione a tabella oltre a quella standard a lista e a timeline. 

Ancora una volta, selezionando una riga, in basso si aprirà la scheda del gioco e potrete fare Join/Leave/Delete

### Aggiungi proponente al tavolo di default
<p><img src="https://github.com/user-attachments/assets/a8044443-9632-4ced-8030-69c01fa6f5be" alt="join toast" height="400"/></p>

E' ora presente un flag che permette, di default, di aggiungere il proponente al tavolo da lui creato.

Se deselezionata, il tavolo verrà creato comunque ma senza aggiungere l'utente allo stesso.

### Inserimento Time Slot (Mattina, Pomeriggio, Sera, Notte) in Creation
<p><img src="https://github.com/user-attachments/assets/2fe06532-bc69-417f-84c0-0f8ee4ab6af4" alt="join toast" height="400"/></p>

Per semplificare la parte di crezione e velocizzarla, l'orario è stato sostituito con dei Time Slot (mattina, pomeriggio, sera, notte).

In fase di Edit è comunque ancora possibile selezionare l'orario desiderato con la consueta precisione di mezz'ora (08:30, 09:00, 09:30...) 

### Utilizzo toast/notifiche per creazione/join/rimozione/delete
<p><img src="https://github.com/user-attachments/assets/16183656-9053-49be-af19-8b18458ad6db" alt="leave toast" width="300"/></p>
<p><img src="https://github.com/user-attachments/assets/d549927b-021f-4323-a9b8-eb2ddc864217" alt="join toast" width="300"/></p>

I messaggi di successo e conseguente aggiornamento sono stati sostituiti con delle notifiche per maggiore reattività della pagina.

Disponibili per: 
 - Creazione (ora il suo messaggio si successo in basso è inoltre permanente per evitare creazioni doppie)
 - Join
 - Leave
 - Delete
 
### Inserimento username
![image](https://github.com/user-attachments/assets/728ae551-418b-49ab-97b9-26f0cb589071)

1. Se non è visibile, espandere la sidebar sulla sinistra,
2. inserire un username nella casella di testo apposita e premere INVIO.
3. L'applicazione ora vi identificherà con quell'username e vi abiliterà le opzioni di: 
   - creazione di una proposta (o tavolo) 
   - unione ad una proposta (o tavolo)
### Creazione di una proposta/tavolo (richiede inserimento username)
![image](https://github.com/user-attachments/assets/a4ecaf84-141b-4733-b423-7a299a539be3)

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
![image](https://github.com/user-attachments/assets/8d47f80a-147f-4ac0-ad31-8db03f0e97a6)

1. Accedere alla tab apposita (la prima)
2. Scorrere tra le proposte (in ordine di creazione)
### Unione ad una proposta/tavolo (richiede inserimento username)
![image](https://github.com/user-attachments/assets/5546a289-807a-4254-b949-56196c78e11a)

1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Join Table X"

NB: 
- Puoi accedere solo una volta ad ogni tavolo con uno specifico username
- Se invece del bottone viene mostrato un messaggio "Set a username to join a table", espandere la sidebar e impostare l'username come indicato sopra
### Rimozione di un utente da un tavolo 
![image](https://github.com/user-attachments/assets/241a43e0-823b-49a9-9593-9be568157ec1)

1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Leave" in corrispndenza dell'utente che si desidera rimuovere
### Rimozione di una proposta
![image](https://github.com/user-attachments/assets/87c376b0-c57f-4a7e-bd3e-e617ccec286f)

1. Accedere alla tab apposita (la prima)
2. Individuare una delle proposte
3. Cliccare su "Delete proposition" 

NB: 
 - Per ragioni di sicurezza, possono essere rimossi solo i tavoli vuoti
 - Elimina tutti i giocatori prima di rimuovere il tavolo se ve ne è qualcuno 
### (OPZIONALE) Invio notifica su un canale Telegram dedicato

![image](https://github.com/user-attachments/assets/9e38d50c-fa2e-4ccf-bf38-519b69532097)

Valorizzando le variabili d'ambiente 
 - TELEGRAM_CHAT_ID
 - TELEGRAM_BOT_TOKEN

Una notifica sul rispettivo canale (chat id/channel id) verrà inviata automaticamente: 
 - al momento della creazione di un tavolo


### (OPZIONALE) Data precompilata
![image](https://github.com/user-attachments/assets/4fb6777c-46f2-4356-992e-f34f96f49b0e)

Valorizzando le variabili d'ambiente
 - DEFAULT_DATE

il selettore della data nella tab di creazione verrà inizializzato a quel valore.

ATTENZIONE: il formato deve essere YYYY-MM-DD, es: 2024-09-29

### Vista Timeline
![image](https://github.com/user-attachments/assets/51d675af-bc5e-4a91-892a-668197ea8270)
Usando l'apposito selettore nella sidebar, si può passare da una visualizzazione come lista ad una a timeline.

Utile per apprezzare la sequenzialità dei vari tavoli 

### Vista filtrata per i soli tavoli a cui mi sono unito (joined)
![image](https://github.com/user-attachments/assets/a9009733-de74-4c3f-8473-a194e9a1e5a9)
Usando il toggle, la vista (che sia lista o timeline) viene filtrata per i SOLI TAVOLI a cui ci si è uniti (joined)

NB: richiede l'inserimento dell'username, altrimenti il toggle è disattivato

### Modifica Tavolo
![image](https://github.com/user-attachments/assets/bb1d99c0-9b30-4953-bec7-3dbf5261ff73)
Usando il tasto "Edit" disponibile sotto ogni gioco, è possibile aprire una finestra per modificare alcune voci del gioco selezionato: 
 - Numero massimo di giocatori (Max Players)
 - Durata (in ore) (Duration)
 - Data (Date)
 - Ora (Time)
 - Note (Notes)

Clicca poi "Update" per applicare le modifiche

NB: **Non è possibile modificare** il **nome** del tavolo e il **BGG game id** 

# English
