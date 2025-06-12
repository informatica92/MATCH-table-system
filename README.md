# MATCH Table System
<p align='center'><img src="https://github.com/informatica92/MATCH-table-system/blob/4c28fe477478bd7fca8dfa09bff6038fb216333e/static/images/table_system_logo.png" alt="logo" height="250"/></p>

This Streamlit app allows users to manage and join board game reservations. Users, once logged in, can create new table propositions specifying game name, duration and number of allowed players; there is also a dedicated page to view all the available tables and join them.
The view page supports multiple view modes: list, timeline and table and integrate above mentioned user settings with BGG game information like image, category and mechanics.
The system is also connected to a Telegram bot that can send notification to a given community when determined events occur (for example table creation)


https://github.com/user-attachments/assets/c912f9c9-cff5-4aaf-acea-162151b3803f

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

| Section               | Variabile d'ambiente                 | Descrizione                                                                                                                                            | Default               | Obbligatorio |
|-----------------------|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------|--------------|  
| # POSTGRESQL DATABASE | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | DB_HOST                              | Hostname del database                                                                                                                                  | localhost             | No           |
|                       | DB_NAME                              | Nome del database                                                                                                                                      |                       | Sì           |
|                       | DB_USER                              | Username del database                                                                                                                                  |                       | Sì           | 
|                       | DB_PASSWORD                          | Password del database                                                                                                                                  |                       | Sì           |
|                       | DB_PORT                              | Porta del database                                                                                                                                     | 5432                  | No           |
|                       | DB_SCHEMA                            | Schema del database (pre esistente)                                                                                                                    | public                | No           |
| # TELEGRAM            | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | TELEGRAM_CHAT_ID                     | Chat ID di Telegram a cui inviare messaggi                                                                                                             |                       | No           |
|                       | TELEGRAM_BOT_TOKEN                   | Token del bot di Telegram, se mancante, non viene effettuato alcun invio                                                                               |                       | No           |
|                       | TELEGRAM_CHAT_ID_PROPOSITION_DEFAULT | Chat ID di Telegram a cui inviare messaggi nel caso delle proposition nella location di default                                                        | TELEGRAM_CHAT_ID      | No           |
|                       | TELEGRAM_CHAT_ID_PROPOSITION_ROW     | Chat ID di Telegram a cui inviare messaggi nel caso delle proposition nelle location custom (system e user ma non default)                             | TELEGRAM_CHAT_ID      | No           |
|                       | TELEGRAM_CHAT_ID_TOURNAMENT          | Chat ID di Telegram a cui inviare messaggi nel caso di Tornei                                                                                          | TELEGRAM_CHAT_ID      | No           |
|                       | TELEGRAM_CHAT_ID_DEMO                | Chat ID di Telegram a cui inviare messaggi nel caso di Demo                                                                                            | TELEGRAM_CHAT_ID      | No           |
| # MAP                 | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | GMAP_MAP_URL                         | URL della mappa di Google Maps, se mancante non viene mostrata alcuna mappa                                                                            |                       | No           |
| # GENERAL SETTINGS    | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | TITLE                                | Titolo dell'applicazione                                                                                                                               | Board Game Proposals  | No           |
|                       | REST_OF_THE_WORLD_PAGE_NAME          | Nome della pagina mostrato nella sidebar e in alcuni commenti. NB: il path rimane sempre "/restofthewrold"                                             | Rest of the World     | No           |
|                       | DURATION_MINUTES_STEP                | Durante la creazione o la modifica di un tavolo, quale sia lo step in termini di minuti che è ammesso per la definizione della DURATA                  | 30 (mins)             | No           |
|                       | LOGO                                 | URL del logo dell'applicazione                                                                                                                         |                       | Sì           |
|                       | LOGO_LARGE                           | URL del logo grande dell'applicazione, se mancante viene usato come logo della sidebar il logo in LOGO                                                 |                       | No           |
|                       | DEFAULT_DATE                         | Data predefinita per la creazione di un tavolo nel formato `YYYY-MM-DD`, se mancante o nel passato, viene usata la data odierna                        | *data odierna*        | No           |
|                       | BASE_URL                             | Il base URL in cui è running l'applicazione (per i link telegram e altro)                                                                              | http://localhost:8501 | No           |
|                       | DONATION_USER                        | Lo username della pagina Ko-fi da mostrare per donazioni/supporto                                                                                      | informatica92         | No           |
|                       | CAN_ADMIN_CREATE_TOURNAMENT          | Se gli ADMIN possono creare proposte di tipo TOURNAMENT (attiva anche la pagina corrispondente)                                                        | false                 | No           |
|                       | CAN_ADMIN_CREATE_DEMO                | Se gli ADMIN possono creare proposte di tipo DEMO (attiva anche la pagina corrispondente)                                                              | false                 | No           |
| # DEFAULT LOCATION    | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | DEFAULT_LOCATION_ALIAS               | L'alias (nome breve e parlante) della location principale del sistema (es "MATCH")                                                                     |                       |              |
|                       | DEFAULT_LOCATION_COUNTRY             | Il Paese in cui è presente la location principale del sistema (es: "Italia")                                                                           |                       |              |
|                       | DEFAULT_LOCATION_CITY                | La città in cui è presente la location principale del sistema (es: "Bari")                                                                             |                       |              |
|                       | DEFAULT_LOCATION_STREEN_NAME         | L'indirizzo in cui è presente la location principale del sistema (es: "via XX Settembre")                                                              |                       |              |
|                       | DEFAULT_LOCATION_STREEN_NUMBER       | Il numero civico in cui è presente la location principale del sistema (es: "18")                                                                       |                       |              |
|                       | CAN_USERS_SET_LOCATION               | Se gli utenti possono scegliere una location diversa da quella principale in fase di Creazione ("true"/"false")                                        | false                 | No           |
| [auth]                | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | redirect_uri                         | URI di reindirizzamento per l'autenticazione, può essere: <br/> - http://localhost:8501/oauth2callback <br/> - https://`dominio deploy`/oauth2callback |                       | Sì           |
|                       | cookie_secret                        | Nome del cookie in cui inserire il token di autenticazione                                                                                             |                       | Sì           |
| [auth.auth0]          | ---                                  | ---                                                                                                                                                    | ---                   | ---          |
|                       | client_id                            | Client ID di Auth0                                                                                                                                     |                       | Sì           |
|                       | client_secret                        | Client Secret di Auth0                                                                                                                                 |                       | Sì           |
|                       | server_metadata_url                  | URL del server metadata di Auth0, nella forma https://`dominio auth0`.com/.well-known/openid-configuration                                             |                       | Sì           |

NB: Alcune "Section" iniziando con `#` sono commenti e non vengono considerate, servo solo a scopo di organizzazione del file.

Le "Section" che invece hanno forma `[nome]` sono obbligatorie e devono essere rispettate.

7. Eseguire
 ```
 streamlit run board_game_manager.py
 ```
## Funzionalità

### 🎉 Novità: Link a Ko-fi per donazioni
<p><img src="https://github.com/user-attachments/assets/1472e494-813d-40e9-992b-92f71653a202" alt="kofi" max-height="400"/></p>

Ora è possibile accedere, tramite apposito bottone presente sempre nella sidebar e in altre location chiave, ad una pagina di Ko-fi nella quale è possibile effettuare donazioni spontanee e volontaree per supportare lo sviluppo e il mantenimento del server APP e il suo DB.

Minimo 1€ (che neanche un caffè, dai)

### 🎉 Novità: Check delle sovrapposizioni (Overlaps)
<p><img src="https://github.com/user-attachments/assets/7bd795d7-8c38-4cb4-b8a9-7a90cf3b53e5" alt="overlaps" max-height="400"/></p>

Ora è disponibile un check in alto che permette di avere una panoramica su eventuali sovrapposizioni dei vari tavoli a cui ci si è uniti.

Il sistema riconosce tre casistiche: 
 - **No Overlaps**: i tavoli a cui ci si è uniti non sono sovrapposti
 - **Important**: due tavoli a cui ci si è uniti hanno la medesima data di inizio
 - **Warning**: due tavoli a cui ci si è uniti hanno una sovrapposizione parziale

Important e Warning sono aggregati in termini di numero se il popover è compresso e l'icona è quella della gravità più alta presente (punto esclamativo se c'è almeno un errore, warning se non ci sono errori ma almeno un warning).

Espandendo il popover si ha poi il detagli delle coppie di tavoli e si può navigare direttamente verso uno di questi per rimuovers, spostare il tavolo...

NB: Il "Go to Table" è disponibile solo nella modalità di visualizzazione "LISTA"

<p><img src="https://github.com/user-attachments/assets/b9f50a7b-a7f7-417b-8484-96d452fb8380" alt="overlaps-ex" max-height="200"/></p>


### 🎉 Novità: Aggiunta delle modalità Tournament e Demo
<p><img src="https://github.com/user-attachments/assets/55f5a354-37f6-4958-98ce-5ded51f70e7d" alt="overlaps" max-height="400"/></p>

E' disponibile ora il concetto di "Proposition Type". Un tavolo può essere dei seguenti tipi:
 - **PROPOSITION**: tutti i tavoli creati dagli utenti, che siano nella location di sistema, user location o system location
 - **TOURNAMENT**: se abilitato tramite la variabile d'ambiente CAN_ADMIN_CREATE_TOURNAMENT, gli admin (e solo gli admin) potranno creare tavoli di tipo TOURNAMENT
 - **DEMO**: se abilitato tramite la variabile d'ambiente CAN_ADMIN_CREATE_DEMO, gli admin (e solo gli admin) potranno creare tavoli di tipo DEMO

TOURNAMENT e DEMO hanno poi, se abilitati, delle pagine dedicate.

Tutti gli utenti potranno comunque unirsi a questi tavoli

Inoltre ora è anche possibile differenziare le destinazioni delle **notifiche Telegram** sulla base della tipologia di proposta e della location:
 - **TELEGRAM_CHAT_ID_PROPOSITION_DEFAULT**: dove inviare le proposte base nella location di default (se assente si userà TELEGRAM_CHAT_ID)
 - **TELEGRAM_CHAT_ID_PROPOSITION_ROW**: dove inviare le proposte base nelle location NON di default (se assente si userà TELEGRAM_CHAT_ID)
 - **TELEGRAM_CHAT_ID_TOURNAMENT**: dove inviare le proposte TOURNAMENT (se assente si userà TELEGRAM_CHAT_ID)
 - **TELEGRAM_CHAT_ID_DEMO**: dove inviare le proposte DEMO (se assente si userà TELEGRAM_CHAT_ID)

Tutte le variabili d'ambiente che riportano una destinazione Telegram possono avere le seguenti forme:
 - **personal** - "123456789"
 - **gruppo** - "-100123456789" -> "-100123456789_1" -> General
 - **gruppo + topic** - "-100123456789_4" 

### 🎉 Novità: Visualizzazione dei tavoli migliorata
<p><img src="https://github.com/user-attachments/assets/f8f9dd41-4af7-49b5-8c76-758fa57ee986" alt="expansions" height="400"/></p>

Con lo scopo di incrementare la leggibilità e allo stesso tempo avere una maggiore compattezza della vista (non influenzata dalla lunghezza di Espansioni e Note), l'interfaccia è stata aggiornata con degli Expander che di default visualizzano una preview dell'informazione ma, se espansi, permettono di accedere ad ulteriori dettagli. 

Ad esempio:
| Campo           | Visualizzazione Compatta   | Visualizzazione Espansa           |
|:----------------|:---------------------------|:----------------------------------|
| **Proposed By** | Username                   | Telegram e BGG username con link  |  
| **Expansions**  | Numero di Espansioni       | La lista di espansioni            |
| **Notes**       | Primi caratteri            | L'intera nota                     |

### Gestione delle Espansioni
<p><img src="https://github.com/user-attachments/assets/9d14ad22-6b10-47af-8a12-b86aa870bf9e" alt="expansions" height="400"/></p>

E' ora possibile aggiungere espansioni ai giochi, in modo da poter specificare quali espansioni saranno utilizzate durante la partita.

Le espansioni selezionate in fase di "Create" vengono poi mostrate nella pagine "View & Join"

E' anche possibile modificare le espansioni in seguito utilizzando il tasto "Edit" disponibile sotto ogni proposta.

### Le Tabs sono ora Pages
<p><img src="https://github.com/user-attachments/assets/6394b19d-08e8-4ede-8227-ca28c6739ab4" alt="tabs vs pages" height="180" width="800"/></p>

Quelle che precedentemente erano tabs (destra nell'immagine) ora sono state trasformate in pagine (sinistra nell'immagine), per una navigazione più fluida e intuitiva

Seleziona una pagina dal menu a sinistra, all'interno della sidebar, per accedere alle funzionalità desiderate

### Login
<p><img src="https://github.com/user-attachments/assets/111d3ec2-7f21-45fa-b3f7-979ec0fe80b0" alt="login" height="400"/></p>
D'ora in avanti agli utenti sarà richiesto di effettuare un "Login" al sistema. Questo renderà più robusta l'intera piattaforma garantendo maggiore controllo.

Al primo accesso verrà creato un utente che non avrà alcun username. Per impostare un username (e quindi abilitare la creazione e l'unione ai tavoli) è necessario recarsi alla page "User" (vedi "Nuova pagina "User"") ed inserire l'username.

ATTENZIONE: L'username è univoco! Non vi sarà quindi possibile selezionare un nome utente già in uso da un altro user.

Il provider principale di autenticazione è Auth0 ma sono offerti anche i seguenti social providers:
 - Google

### Nuova pagina "User"
<p><img src="https://github.com/user-attachments/assets/be58f0b5-8f3c-42c5-b9fd-340c60d39b27" alt="user page" height="400"/></p>

E' ora possibile accedere ad una pagina interamente dedicata all'utente in cui è possibile impostare campi come:
 - Nome
 - Cognome
 - Username
 - Telegram username
 - BGG username

ATTENZIONE: L'username è univoco! Non vi sarà quindi possibile selezionare un nome utente già in uso da un altro user.

ATTENZIONE: L'username è inoltre necessario per abilitare creazione e unione ai tavoli.

### Funzionalità "Locations"
<p><img src="https://github.com/user-attachments/assets/c0755854-42f3-41c4-a87d-0f7f53413ea5" alt="user page" height="400"/></p>

A parte le location di sistema, ogni utente può ora aggiungere una o più location in cui è disponibile a giocare.

Le Location di Sistema (Admin Locations) sono gestibili solo dagli utenti Admin. Si tratta di una impostazione a livello DB.

In fase di creazione di un tavolo, nella pagina "Create", è possibile selezionare la location nella quale si terrà il tavolo: 
 - in occasione degli eventi MATCH, usare quindi la location (di sistema) "MATCH"
 - se lo si desidera, sarà quindi possibile aprire tavoli anche durante tutto l'anno con le location delle varie altre associazioni (es "Masseria Andriani", "Biblioteca di Putignano", "Officina dei Saperi"...)

ATTENZIONE: le location di sistema appariranno sempre a tutti gli utenti e sono quindi trasversali, le location utente, invece, possono essere usate come location solo dall'utente che l'ha creata.

### (OPZIONALE) Invio notifica su un canale Telegram dedicato

<p><img src="https://github.com/user-attachments/assets/1c3af6b9-63ec-4867-aa89-831e861af4cb" alt="user page" height="400"/></p>

Valorizzando le variabili d'ambiente 
 - TELEGRAM_CHAT_ID
 - TELEGRAM_BOT_TOKEN

Una notifica sul rispettivo canale (chat id/channel id) verrà inviata automaticamente: 
 - al momento della creazione di un tavolo

### Delete ora con finestra di conferma e permette eliminazione di tavoli con 1+ giocatori
<p><img src="https://github.com/user-attachments/assets/b3589ef2-7869-43fa-9f53-94d2d6562e5a" alt="join toast" max-height="400"/></p>

Delete ha ora una finestra di conferma e permette anche l'eliminazione di tavoli con 1+ giocatori

### Leave/Delete/Edit possibili solo per sè stessi e per i propri tavoli
<p><img src="https://github.com/user-attachments/assets/53569a54-15a5-4961-b48d-a4fef435f709" alt="join toast" max-height="400"/></p>

Leave/Delete/Edit possibili solo per sè stessi e per i propri tavoli: 
 - Leave è quindi abilitata solo per sè stessi e per i giocatori ai propri tavoli
 - Delete/Edit è quindi possibile solo per i propri tavoli 

### GOD MODE introdotta per rendere Leave/Delete/Edit possibili sempre
<p><img src="https://github.com/user-attachments/assets/2c133444-8b32-46a0-bc41-ae115bf36d71" alt="join toast" max-height="400" /></p>

La GOD MODE permette, in caso di opportuna configurazione dell'utenta da parte degli amministratori, di superare il vincolo per cui Leave/Delete/Edit è possibile solo per sè stessi e per i propri tavoli.

Utile per testing e manutenzione

### Vista a Tabella
<p><img src="https://github.com/user-attachments/assets/9d5dd314-2af6-4d2d-9114-5d3464e9d993" alt="join toast" max-height="400"/></p>

E' stata aggiunta una visualizzazione a tabella oltre a quella standard a lista e a timeline. 

Ancora una volta, selezionando una riga, in basso si aprirà la scheda del gioco e potrete fare Join/Leave/Delete

### Aggiungi proponente al tavolo di default
<p><img src="https://github.com/user-attachments/assets/a8044443-9632-4ced-8030-69c01fa6f5be" alt="join toast" max-height="400"/></p>

E' ora presente un flag che permette, di default, di aggiungere il proponente al tavolo da lui creato.

Se deselezionata, il tavolo verrà creato comunque ma senza aggiungere l'utente allo stesso.

### Inserimento Time Slot (Mattina, Pomeriggio, Sera, Notte) in Creation
<p><img src="https://github.com/user-attachments/assets/2fe06532-bc69-417f-84c0-0f8ee4ab6af4" alt="join toast" max-height="400"/></p>

Per semplificare la parte di crezione e velocizzarla, l'orario è stato sostituito con dei Time Slot (mattina, pomeriggio, sera, notte).

In fase di Edit è comunque ancora possibile selezionare l'orario desiderato con la consueta precisione di mezz'ora (08:30, 09:00, 09:30...) 

### Utilizzo toast/notifiche per creazione/join/rimozione/delete
<p><img src="https://github.com/user-attachments/assets/16183656-9053-49be-af19-8b18458ad6db" alt="leave toast" max-width="300"/></p>
<p><img src="https://github.com/user-attachments/assets/d549927b-021f-4323-a9b8-eb2ddc864217" alt="join toast" max-width="300"/></p>

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
 - Durata (in minuti) (Duration)
 - Data (Date)
 - Ora (Time)
 - Note (Notes)

Clicca poi "Update" per applicare le modifiche

NB: **Non è possibile modificare** il **nome** del tavolo e il **BGG game id** 

# English
