# Guida al Deploy — Smart CRM

Stack: **Supabase** (DB) · **Fly.io** (Django + FastAPI unificati) · **Vercel** (Nuxt)

Django e FastAPI girano nello **stesso servizio Fly.io**: Django gestisce `/api/*`,
FastAPI gestisce `/ai/*` e `/reports/*`. Un solo container, una sola porta.

Tempo stimato: 1-2 ore la prima volta.

---

## Prerequisiti

Installa questi strumenti sul tuo computer:

```bash
# Fly CLI
curl -L https://fly.io/install.sh | sh

# Vercel CLI
npm i -g vercel
```

Crea account su:
- https://supabase.com
- https://fly.io
- https://vercel.com

---

## FASE 1 — Supabase (Database)

### 1.1 Crea il progetto

1. Vai su https://supabase.com → **New project**
2. Nome: `smart-crm`
3. Scegli password DB (salvala, ti serve dopo)
4. Regione: **Frankfurt** (EU West)
5. Clicca **Create new project** e aspetta ~2 minuti

### 1.2 Abilita pgvector

1. Nel pannello Supabase → **SQL Editor**
2. Incolla ed esegui:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Clicca **Run** → deve comparire "Success"

### 1.3 Prendi le credenziali DB

1. Vai su **Project Settings → Database**
2. Nella sezione **Connection parameters** prendi:
   - Host: `db.XXXXXXXX.supabase.co`
   - Database name: `postgres`
   - User: `postgres`
   - Password: quella che hai scelto al punto 1.1
   - Port: `5432`

---

## FASE 2 — Fly.io (Django + FastAPI)

### 2.1 Login e crea l'app

```bash
# Entra nella root del progetto (non in backend/)
cd smart-crm

flyctl auth login
flyctl apps create smart-crm-backend
```

Se `smart-crm-backend` è già preso, scegli un altro nome e aggiornalo in `backend/fly.toml`.

### 2.2 Crea il volume per i file allegati

```bash
flyctl volumes create media_data \
  --app smart-crm-backend \
  --region fra \
  --size 3
```

### 2.3 Genera una SECRET_KEY sicura

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copia l'output — ti serve nel prossimo step e deve essere **la stessa** per Django e FastAPI.

### 2.4 Imposta le variabili d'ambiente

```bash
flyctl secrets set \
  SECRET_KEY="incolla-qui-la-chiave-generata" \
  DJANGO_SECRET_KEY="incolla-qui-la-stessa-chiave" \
  DEBUG="False" \
  ALLOWED_HOSTS="smart-crm-backend.fly.dev" \
  DB_HOST="db.XXXXXXXX.supabase.co" \
  DB_NAME="postgres" \
  DB_USER="postgres" \
  DB_PASSWORD="la-tua-password-supabase" \
  DB_PORT="5432" \
  CORS_ALLOWED_ORIGINS="https://smart-crm.vercel.app" \
  ALLOWED_ORIGINS="https://smart-crm.vercel.app" \
  --app smart-crm-backend
```

> `CORS_ALLOWED_ORIGINS` è per Django · `ALLOWED_ORIGINS` è per FastAPI · devono contenere lo stesso URL Vercel.
> Aggiorna entrambi con l'URL reale dopo il deploy del frontend (Fase 3).

### 2.5 Deploy

Assicurati di essere nella root del progetto (`smart-crm/`), non in `backend/`:

```bash
cd smart-crm
flyctl deploy --config backend/fly.toml
```

La prima volta impiega 4-6 minuti. Alla fine:

```
✓ Machine ... is now in a running state
```

### 2.6 Crea il superuser Django

```bash
flyctl ssh console --app smart-crm-backend --command "python manage.py createsuperuser"
```

Inserisci username, email e password quando richiesto.

### 2.7 Verifica

```bash
# Django
curl https://smart-crm-backend.fly.dev/api/

# FastAPI
curl https://smart-crm-backend.fly.dev/health
# risposta: {"status":"ok"}
```

---

## FASE 3 — Vercel (Frontend Nuxt)

### 3.1 Pusha il codice su GitHub

```bash
cd smart-crm
git add .
git commit -m "config: deploy files"
git remote add origin https://github.com/TUO-USERNAME/smart-crm.git
git push -u origin main
```

### 3.2 Connetti il repo a Vercel

1. Vai su https://vercel.com → **Add New Project**
2. Seleziona il repo `smart-crm`
3. **Root Directory**: imposta `frontend`
4. Framework: Vercel rileva automaticamente **Nuxt**
5. Non cliccare ancora Deploy

### 3.3 Imposta le variabili d'ambiente su Vercel

| Nome | Valore |
|------|--------|
| `NUXT_PUBLIC_API_BASE` | `https://smart-crm-backend.fly.dev/api` |
| `NUXT_PUBLIC_AI_BASE` | `https://smart-crm-backend.fly.dev` |

Nota: entrambe puntano allo **stesso dominio Fly.io**. Il frontend chiama:
- Django → `https://smart-crm-backend.fly.dev/api/...`
- FastAPI → `https://smart-crm-backend.fly.dev/ai/...`

### 3.4 Deploy

Clicca **Deploy**. Impiega 2-3 minuti.

Al termine ricevi un URL tipo `https://smart-crm-XXXX.vercel.app`.

### 3.5 Aggiorna CORS su Fly.io con l'URL definitivo

```bash
flyctl secrets set \
  CORS_ALLOWED_ORIGINS="https://smart-crm-XXXX.vercel.app" \
  ALLOWED_ORIGINS="https://smart-crm-XXXX.vercel.app" \
  --app smart-crm-backend
```

Fly.io riavvia il container automaticamente.

---

## FASE 4 — Verifica finale

1. Apri l'URL Vercel nel browser
2. Login con le credenziali del superuser (passo 2.6)
3. Importa un file Excel di test
4. In **Impostazioni** inserisci una API key Anthropic o OpenAI
5. Apri la chat AI e fai una domanda

---

## Aggiornamenti futuri

```bash
# Ogni modifica al codice:
cd smart-crm
git add . && git commit -m "update"
git push  # Vercel fa redeploy automatico del frontend

# Backend (quando modifichi Django o FastAPI):
flyctl deploy --config backend/fly.toml
```

---

## Problemi comuni

**"relation does not exist" al primo avvio**
Le migrazioni non sono girate. Controlla i log:
```bash
flyctl logs --app smart-crm-backend
```

**CORS error nel browser**
L'URL di Vercel non è in `CORS_ALLOWED_ORIGINS`. Ripeti il passo 3.5.

**"No API key configured" nella chat AI**
Normale. Ogni utente inserisce la propria chiave Anthropic/OpenAI in Impostazioni.

**Supabase "project paused"**
Accade se non usate l'app per 7 giorni. Vai su Supabase → **Restore project**.

**Aggiornare un secret**
```bash
flyctl secrets set NOME="nuovo-valore" --app smart-crm-backend
# Il container si riavvia automaticamente
```
