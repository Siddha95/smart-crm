# Smart CRM

CRM dinamico con supporto AI, costruito su Django, FastAPI e Nuxt 3.

Ogni utente ha il proprio spazio isolato: importa file Excel, gestisce i record, carica allegati e interroga i dati tramite un assistente AI.

---

## Architettura

```
smart-crm/
├── backend/        # API REST — Django + PostgreSQL
├── ai-service/     # Servizio AI — FastAPI + RAG con pgvector
└── frontend/       # Interfaccia — Nuxt 3 + Nuxt UI
```

I tre servizi comunicano così:
- Il **frontend** chiama il **backend** per tutte le operazioni sui dati
- Il **frontend** chiama l'**ai-service** per chat e reportistica AI
- L'**ai-service** accede direttamente a PostgreSQL in sola lettura per le query vettoriali

---

## Funzionalità

- **Import Excel** — carica file `.xlsx`, ogni foglio diventa una sezione del CRM
- **Tabella dinamica** — colonne generate automaticamente dal file importato, con sorting e ricerca globale
- **Dettaglio record** — form di modifica, allegati (foto/PDF), storico modifiche campo per campo
- **Isolamento per utente** — ogni utente vede solo i propri dati
- **AI Assistente** — chat contestuale sui propri dati tramite RAG (solo i record rilevanti vengono inviati al modello)
- **Provider AI agnostico** — supporta Claude (Anthropic) e GPT (OpenAI), configurabile via `.env`

---

## Requisiti

- Python 3.11+
- Node.js 20+
- PostgreSQL 17 con estensione `pgvector`

---

## Setup

### 1. Database

```bash
# Avvia PostgreSQL
pg_ctl -D /usr/local/var/postgresql@17 start

# Crea il database
createdb smart_crm

# Abilita pgvector
psql smart_crm -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Backend

```bash
cd backend

# Crea e attiva il virtualenv
python -m venv venv
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con i tuoi valori

# Applica le migrazioni
python manage.py migrate

# Crea il superuser
python manage.py createsuperuser

# Avvia il server
python manage.py runserver
```

Il backend è disponibile su `http://localhost:8000`.

### 3. AI Service

```bash
cd ai-service

# Installa le dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
cp .env.example .env
# Inserisci almeno una API key (CLAUDE_API_KEY o OPENAI_API_KEY)
# OPENAI_API_KEY è necessaria anche per gli embeddings RAG

# Avvia il servizio
uvicorn main:app --reload --port 8001
```

L'AI service è disponibile su `http://localhost:8001`.
Documentazione API: `http://localhost:8001/docs`.

### 4. Frontend

```bash
cd frontend

# Installa le dipendenze
npm install

# Configura le variabili d'ambiente
cp .env.example .env

# Avvia il server di sviluppo
npm run dev
```

Il frontend è disponibile su `http://localhost:3000`.

---

## Variabili d'ambiente

### Backend (`backend/.env`)

| Variabile | Descrizione |
|-----------|-------------|
| `SECRET_KEY` | Chiave segreta Django |
| `DEBUG` | `True` in sviluppo, `False` in produzione |
| `ALLOWED_HOSTS` | Host consentiti (es. `localhost,127.0.0.1`) |
| `DB_NAME` | Nome del database PostgreSQL |
| `DB_USER` | Utente PostgreSQL |
| `DB_PASSWORD` | Password PostgreSQL |
| `DB_HOST` | Host PostgreSQL (default: `localhost`) |
| `DB_PORT` | Porta PostgreSQL (default: `5432`) |
| `OPENAI_API_KEY` | API key OpenAI per la generazione degli embeddings |

### AI Service (`ai-service/.env`)

| Variabile | Descrizione |
|-----------|-------------|
| `CLAUDE_API_KEY` | API key Anthropic (prioritaria se presente) |
| `OPENAI_API_KEY` | API key OpenAI (usata anche per gli embeddings) |
| `DB_NAME` | Nome del database PostgreSQL |
| `DB_USER` | Utente PostgreSQL |
| `DB_PASSWORD` | Password PostgreSQL |
| `DB_HOST` | Host PostgreSQL (default: `localhost`) |
| `DB_PORT` | Porta PostgreSQL (default: `5432`) |

---

## Stack tecnico

| Layer | Tecnologie |
|-------|-----------|
| Backend | Django 6, Django REST Framework, SimpleJWT, pgvector |
| AI Service | FastAPI, SQLAlchemy, Anthropic SDK, OpenAI SDK |
| Frontend | Nuxt 3, Nuxt UI, Pinia, TanStack Table |
| Database | PostgreSQL 17 + pgvector |
| Auth | JWT (access + refresh token) |
