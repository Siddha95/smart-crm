# Smart CRM — Prospetto per nuovi sviluppatori

> Leggi questo documento se sei appena entrato nel team. Ti spiega tutto il progetto dall'alto verso il basso.

---

## 1. Cos'è questo progetto

**Smart CRM** è un'applicazione web per gestire contatti, clienti e pipeline di vendita.
Permette di importare file Excel, visualizzare i dati in tabella o kanban, allegare file, aggiungere commenti, e usare un assistente AI per interrogare i dati in linguaggio naturale.

---

## 2. Architettura ad alto livello

Il progetto è composto da **tre servizi separati**:

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                              │
│              Nuxt 4 + Vue 3 (frontend)                      │
│                   localhost:3000                             │
└──────────────┬───────────────────────┬──────────────────────┘
               │ HTTP / REST (JWT)     │ HTTP / REST (JWT)
               ▼                       ▼
┌──────────────────────┐   ┌───────────────────────────────┐
│   Django + DRF       │   │   FastAPI (ai-service)        │
│   localhost:8000     │   │   localhost:8001              │
│                      │   │                               │
│  - Autenticazione    │   │  - Chat AI (Claude/OpenAI)    │
│  - CRUD dati CRM     │   │  - Ricerca vettoriale         │
│  - Import Excel      │   │  - Analisi record             │
│  - Export XLSX/PDF   │   │  - Embeddings                 │
│  - File allegati     │   │                               │
└──────────┬───────────┘   └──────────────┬────────────────┘
           │                              │
           └──────────────┬───────────────┘
                          ▼
              ┌───────────────────────┐
              │   PostgreSQL + pgvector│
              │   (database condiviso) │
              └───────────────────────┘
```

**Punto chiave:** Django e FastAPI **condividono lo stesso database PostgreSQL**. FastAPI non ha una propria autenticazione — legge il JWT emesso da Django e lo verifica con la stessa `SECRET_KEY`.

---

## 3. Struttura delle cartelle

```
smart-crm/
├── backend/               → Django (API principale)
│   ├── config/            → Configurazione Django (settings, urls, wsgi)
│   └── crm/               → App Django con tutta la logica CRM
│       ├── models.py      → Definizione tabelle database
│       ├── serializers.py → Conversione modelli ↔ JSON
│       ├── views.py       → Endpoint API (ViewSet)
│       ├── migrations/    → Storia delle modifiche al DB
│       ├── tests.py       → Test unitari e di integrazione (136 test)
│       └── services/      → Logica di business (import Excel, export, embedding)
│
├── ai-service/            → FastAPI (microservizio AI)
│   ├── main.py            → Entry point FastAPI
│   ├── config.py          → Variabili d'ambiente (pydantic-settings)
│   ├── database.py        → Connessione SQLAlchemy al DB
│   ├── dependencies.py    → Auth JWT + provider AI per ogni richiesta
│   ├── models.py          → Modelli SQLAlchemy (read-only dal DB Django)
│   ├── routers/           → Endpoint: ai.py (chat) e reports.py
│   └── services/          → Provider AI (Claude, OpenAI) e embeddings
│
└── frontend/              → Nuxt 4 + Vue 3
    └── app/
        ├── app.vue        → Layout radice (header, sidebar AI, taccuino)
        ├── pages/         → Pagine (router automatico basato su file)
        │   ├── login.vue
        │   ├── dashboard.vue
        │   ├── import.vue
        │   ├── settings.vue
        │   └── source/[id].vue  → Pagina principale datasource
        ├── components/    → Componenti riutilizzabili
        ├── composables/
        │   └── useApi.ts  → Client HTTP centralizzato
        ├── stores/        → Stato globale Pinia
        │   ├── auth.ts    → Token JWT, login/logout
        │   ├── datasources.ts → Lista datasource
        │   ├── chat.ts    → Storico chat AI
        │   └── notes.ts   → Taccuino note
        └── middleware/
            └── auth.ts    → Protezione route (redirect a /login)
```

---

## 4. Flusso dati: dalla richiesta alla risposta

### Esempio: l'utente apre la pagina di un datasource

```
1. Browser naviga a /source/42

2. Nuxt esegue il middleware auth.ts
   → controlla authStore.isAuthenticated (cookie auth_token presente?)
   → se no: redirect a /login

3. La pagina source/[id].vue viene caricata
   → chiama api.get('/datasources/')     → lista tutti i datasource
   → chiama api.get('/records/?data_source=42') → record del datasource

4. useApi.ts costruisce la richiesta:
   → aggiunge header Authorization: Bearer <token>
   → fetch a http://localhost:8000/api/records/?data_source=42

5. Django riceve la richiesta
   → DRF verifica il JWT con SimpleJWT
   → RecordViewSet.get_queryset() filtra per data_source__owner=request.user
   → restituisce JSON paginato { count, results }

6. Il browser riceve il JSON
   → Vue aggiorna il template reattivamente
   → La tabella mostra i record
```

---

## 5. Sistema di autenticazione

### Flusso di login

```
Utente inserisce username + password
         ↓
login.vue chiama authStore.login()
         ↓
POST /api/auth/token/ → Django SimpleJWT
         ↓
Django restituisce:
  { "access": "eyJ...", "refresh": "eyJ..." }
         ↓
authStore salva i token in cookie (SSR-safe):
  useCookie('auth_token')    → access token  (valido 8 ore)
  useCookie('auth_refresh')  → refresh token (valido 30 giorni)
         ↓
router.push('/dashboard')
```

### Refresh automatico del token

`useApi.ts` gestisce automaticamente la scadenza:

```
Richiesta API → risposta 401
       ↓
Prova a rinnovare: POST /api/auth/token/refresh/
       ↓
  Successo → riprova la richiesta originale con il nuovo token
  Fallito  → authStore.logout() + redirect a /login
```

**Blacklist:** dopo la rotazione, il vecchio refresh token viene blacklistato (non riutilizzabile). Configurato in `settings.py` con `BLACKLIST_AFTER_ROTATION = True`.

### Come FastAPI verifica i token

FastAPI non ha il suo sistema di autenticazione. In `dependencies.py`:

```python
payload = jwt.decode(token, settings.django_secret_key, algorithms=["HS256"])
user_id = payload.get("user_id")
```

Usa la **stessa `SECRET_KEY` di Django** per decodificare il JWT. Il `user_id` estratto viene usato per filtrare i dati nel database.

---

## 6. Separazione Django / FastAPI

| Cosa fare | Usa |
|-----------|-----|
| Login / registrazione | Django |
| CRUD record, datasource, note | Django |
| Import/export Excel | Django |
| File allegati | Django |
| Chat AI con i dati | FastAPI |
| Analisi singolo record | FastAPI |
| Ricerca vettoriale / semantica | FastAPI |
| Suggerimenti azioni AI | FastAPI |

**Regola pratica:** se coinvolge l'AI, va su FastAPI. Tutto il resto va su Django.

Il frontend chiama i due servizi tramite URL diversi:
- `config.public.apiBase` → `http://localhost:8000/api` (Django)
- `config.public.aiBase` → `http://localhost:8001` (FastAPI)

---

## 7. I modelli principali (database)

```
auth_user (Django built-in)
    │
    ├── UserProfile          → chiave API personale, contesto AI
    ├── DataSource           → "foglio Excel" importato (colonne, stages)
    │       └── Record       → riga del datasource (data JSON + embedding)
    │               ├── RecordHistory    → chi ha cambiato cosa e quando
    │               ├── RecordComment    → commenti interni
    │               └── Attachment       → file allegati
    ├── Note                 → taccuino personale (markdown)
    └── StageTemplate        → configurazioni kanban salvate
```

**Punto chiave:** `Record.data` è un campo **JSONField** — ogni riga è un dizionario Python/JSON. Le colonne non sono rigide: si adattano dinamicamente al file Excel importato.

---

## 8. Come funziona l'AI

### Ricerca ibrida

Quando l'utente fa una domanda in chat, FastAPI:

1. **Ricerca vettoriale:** converte la domanda in embedding (OpenAI), cerca i record più simili per coseno nel campo `Record.embedding` (pgvector)
2. **Ricerca full-text:** cerca le parole chiave della domanda nei dati JSON dei record
3. **Deduplicazione:** unisce i risultati, rimuove i duplicati, prende i 12 più rilevanti

### Costruzione del system prompt

```python
system_prompt = (
    "Assistente CRM.\n"
    f"Contesto utente:\n{user_context}\n"   # ← scritto dall'utente in Impostazioni
    "Record disponibili:\n"
    f"{context_rows}\n"
    "Puoi rispondere, modificare campi ed eliminare record con i tool."
)
```

Il **contesto utente** è un testo libero scritto dall'utente nella pagina Impostazioni. Viene iniettato in ogni conversazione senza usare storico — efficiente in termini di token.

### Tool dell'AI

L'AI può eseguire azioni reali sul database:
- `update_record(record_id, field, value)` → modifica un campo JSON
- `delete_record(record_id)` → soft delete (`is_active = False`, non eliminazione fisica)

Entrambe verificano che il record appartenga all'utente autenticato.

---

## 9. File chiave — spiegazione dettagliata

### `backend/crm/models.py`

Definisce tutte le tabelle del database. Punti non ovvi:
- `DataSource.save()` chiama `full_clean()` prima del salvataggio → validazione sempre attiva
- `Record.embedding` è un `VectorField(dimensions=1536)` → vettore numerico per la ricerca semantica
- `Record.position` → intero per l'ordinamento manuale nel kanban
- `UserProfile.ai_context` → testo libero che l'AI legge ad ogni sessione

### `backend/crm/views.py`

Tutti gli endpoint REST. Architettura **ViewSet** di DRF:
- Ogni ViewSet copre automaticamente GET (lista), GET (dettaglio), POST, PATCH, DELETE
- `get_queryset()` filtra **sempre** per `owner=request.user` → isolamento dati tra utenti
- `perform_create()` e `perform_update()` sovrascrivono il salvataggio per aggiungere logica (storico modifiche, data inserimento automatica)
- Le azioni custom usano `@action` decorator (es. `/records/reorder/`, `/datasources/{id}/stages/`)

### `backend/crm/serializers.py`

Convertono i modelli Django in JSON e viceversa:
- `personal_api_key` è `write_only=True` → non viene mai restituita nelle risposte GET
- `has_api_key` è un campo calcolato → l'utente sa se ha una chiave senza vederla

### `frontend/app/composables/useApi.ts`

Client HTTP centralizzato. Tutti i componenti usano questo invece di `fetch` direttamente:
- Aggiunge automaticamente `Authorization: Bearer <token>`
- Gestisce il refresh automatico del token (una sola volta per richiesta)
- In caso di 401 irrecuperabile: logout automatico + redirect a login
- `download()` usa un link temporaneo per scaricare file binari (xlsx, pdf)

### `frontend/app/stores/auth.ts`

Usa `useCookie` invece di `localStorage` per i token → funziona anche lato server (SSR). I cookie vengono inviati automaticamente con le richieste dal browser.

### `ai-service/dependencies.py`

Il cuore dell'autenticazione FastAPI:
- Legge il JWT dall'header `Authorization`
- Verifica la firma con la `django_secret_key`
- Carica il profilo utente da DB per ottenere la chiave API personale
- Costruisce il provider AI corretto (Claude se la chiave inizia con `sk-ant`, OpenAI altrimenti)

---

## 10. Librerie principali

### Backend (Python)

| Libreria | Cosa fa | Perché qui |
|----------|---------|-----------|
| **Django 6** | Framework web MVC | Base dell'API REST, ORM, migrazioni |
| **DRF** (djangorestframework) | REST API toolkit | ViewSet, serializer, autenticazione |
| **SimpleJWT** | JWT per Django | Emette e verifica token di accesso/refresh |
| **pgvector** | Vettori in PostgreSQL | Ricerca semantica sugli embedding dei record |
| **pandas** | Manipolazione dati | Lettura e parsing dei file Excel |
| **openpyxl** | File Excel | Lettura/scrittura .xlsx |
| **fpdf2** | Generazione PDF | Export PDF dei datasource |
| **anthropic** | SDK Claude AI | Client ufficiale per l'API di Claude |
| **openai** | SDK OpenAI | Client per GPT e embedding |
| **FastAPI** | Framework API async | Microservizio AI (più leggero di Django) |
| **SQLAlchemy** | ORM per FastAPI | Accesso al DB PostgreSQL dal microservizio |
| **PyJWT** | Decode JWT in FastAPI | Verifica token Django senza Django |
| **pydantic-settings** | Config da env var | Caricamento sicuro di variabili d'ambiente |

### Frontend (JavaScript/TypeScript)

| Libreria | Cosa fa | Perché qui |
|----------|---------|-----------|
| **Nuxt 4** | Framework Vue SSR | Routing, SSR, build ottimizzata |
| **Vue 3** | Framework UI reattivo | Componenti, reattività, Composition API |
| **Pinia** | State management | Store globali (auth, datasource, chat, note) |
| **Nuxt UI** | Componenti UI | Button, Modal, Table, Slideover pronti all'uso |
| **Tailwind CSS 4** | Utility CSS | Stile inline tramite classi, nessun CSS custom |
| **marked** | Markdown → HTML | Rendering del taccuino note |
| **Lucide** | Icone SVG | Icone uniformi in tutta l'app |

---

## 11. Percorso di apprendimento (learning path)

### Settimana 1 — Basi

1. Leggi `backend/crm/models.py` → capire la struttura dati
2. Leggi `backend/config/urls.py` → capire quali endpoint esistono
3. Prova le API con curl o Insomnia: login → ottieni token → chiama `/api/datasources/`
4. Leggi `frontend/app/composables/useApi.ts` → capire come il frontend chiama le API

### Settimana 2 — Frontend

5. Leggi `frontend/app/stores/auth.ts` → autenticazione e cookie
6. Leggi `frontend/app/pages/login.vue` → flusso di login completo
7. Leggi `frontend/app/pages/dashboard.vue` → come si caricano i datasource
8. Leggi `frontend/app/pages/source/[id].vue` → pagina più complessa dell'app

### Settimana 3 — Backend avanzato

9. Leggi `backend/crm/views.py` → tutti gli endpoint e la logica di filtraggio
10. Leggi `backend/crm/services/excel_import.py` → come funziona l'import
11. Esegui i test: `python manage.py test crm.tests` → capire cosa è testato

### Settimana 4 — AI Service

12. Leggi `ai-service/dependencies.py` → autenticazione e provider AI
13. Leggi `ai-service/routers/ai.py` → flusso della chat (ricerca ibrida + LLM)
14. Leggi `ai-service/services/ai/tools.py` → come l'AI modifica il database

---

## 12. Traccia completa: utente importa un file Excel

Questo trace copre tutto il sistema dall'inizio alla fine.

```
UTENTE: va su /import, seleziona un file Excel, clicca "Importa"
```

**Step 1 — Frontend: anteprima**
```
import.vue → api.upload('/datasources/preview/', formData)
→ POST http://localhost:8000/api/datasources/preview/
→ invia il file come multipart/form-data
```

**Step 2 — Django: anteprima**
```
DataSourceViewSet.preview()
→ salva il file in un file temporaneo
→ chiama preview_sheets(tmp_path)
→ pandas legge i fogli Excel
→ normalizza nomi colonne: str(c).strip()
→ restituisce { sheets: [{ name, columns, rows_preview }] }
→ cancella il file temporaneo
```

**Step 3 — Frontend: conferma**
```
L'utente vede l'anteprima con nomi colonne e righe di esempio
Clicca "Conferma importazione"
→ api.upload('/datasources/upload/', formData)
```

**Step 4 — Django: importazione**
```
DataSourceViewSet.upload()
→ import_all_sheets(tmp_path, owner=request.user)
→ per ogni foglio Excel:
   1. Crea DataSource (name, columns, source_file)
   2. Per ogni riga:
      a. clean_row() → normalizza valori (NaN→None, date→DD/MM/YYYY)
      b. Aggiunge "Data inserimento" con data corrente
      c. Crea Record(data=row_dict)
      d. (Asincrono) calcola embedding via OpenAI e salva in Record.embedding
→ restituisce { imported: 3, datasources: [...] }
```

**Step 5 — Frontend: navigazione**
```
Riceve la risposta con gli ID dei nuovi datasource
dsStore.fetch() → aggiorna la lista in Pinia
router.push('/source/42') → naviga al primo datasource importato
```

**Step 6 — AI: prima domanda**
```
L'utente apre la chat AI e chiede: "Chi sono i clienti di Milano?"

chatStore.send("Chi sono i clienti di Milano?")
→ POST http://localhost:8001/ai/datasources/42/chat
   { "question": "Chi sono i clienti di Milano?" }
   Header: Authorization: Bearer <token>

FastAPI → dependencies.py
→ decodifica JWT con django_secret_key
→ carica UserProfile → ottiene personal_api_key
→ costruisce ClaudeProvider con la chiave dell'utente

FastAPI → routers/ai.py
→ _find_hybrid("Chi sono i clienti di Milano?", db, embedding_provider)
   1. embedding della domanda → vettore 1536 dimensioni
   2. cosine_distance su Record.embedding → top 8 per similarità
   3. ilike "%Milano%" su tutti i record → top 8 full-text
   4. deduplicazione → max 12 record totali

→ _run_chat(question, records, provider, db, owner_id)
   system_prompt = "Assistente CRM.\nContesto utente: [testo utente]\nRecord: [12 righe serializzate]"
   provider.complete_with_tools(messages, tools, system)

Claude risponde con il testo + eventualmente chiama update_record o delete_record

→ risposta: { answer: "Ecco i clienti di Milano: ..." }
```

---

## 13. Cose da sapere prima di modificare il codice

1. **Isolamento dati:** ogni ViewSet Django filtra SEMPRE per `owner=request.user`. Non rimuovere mai quel filtro.

2. **Soft delete AI:** il tool `delete_record` imposta `is_active=False`, non elimina fisicamente. I record "eliminati" restano nel DB per audit.

3. **JSONField flessibile:** `Record.data` non ha schema fisso. Le colonne sono definite in `DataSource.columns`. Quando aggiungi una colonna, il backend aggiorna tutti i record via SQL raw.

4. **Token condiviso:** Django e FastAPI usano la stessa `SECRET_KEY`. Se la cambi, tutti i token esistenti diventano invalidi.

5. **Migrazioni:** dopo ogni modifica ai modelli Django, crea e applica la migrazione:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Test:** prima di fare merge, esegui `python manage.py test crm.tests`. Ci sono 136 test.

7. **Date:** tutto il progetto usa il formato `DD/MM/YYYY` (italiano). La funzione `clean_row()` in `excel_import.py` normalizza tutti i formati date all'import.
