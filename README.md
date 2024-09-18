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
7. Eseguire
 ```
 streamlit run board_game_manager.py
 ```
## Funzionalità
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
