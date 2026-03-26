# Guida al Deploy — Smart CRM

Stack: **Supabase** (DB) · **Oracle Cloud Free Tier** (Django + FastAPI) · **Vercel** (Nuxt)

Costo: **€0/mese** — Oracle Always Free · Supabase gratis · Vercel gratis

---

## Prerequisiti

```bash
npm i -g vercel
```

Account necessari:

- <https://cloud.oracle.com> (già registrato)
- <https://supabase.com>
- <https://vercel.com>

---

## FASE 1 — Supabase (Database)

### 1.1 Crea il progetto

1. Vai su <https://supabase.com> → **New project**
2. Nome: `smart-crm`
3. Scegli password DB (salvala)
4. Regione: **Frankfurt** (EU West)
5. Clicca **Create new project** e aspetta ~2 minuti

### 1.2 Abilita pgvector

1. Nel pannello Supabase → **SQL Editor**
2. Incolla ed esegui:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.3 Prendi le credenziali DB

Vai su **Project Settings → Database → Connection parameters**:

- Host: `db.XXXXXXXX.supabase.co`
- Database name: `postgres`
- User: `postgres`
- Password: quella scelta al punto 1.1
- Port: `5432`

---

## FASE 2 — Oracle Cloud Free Tier (VM)

### 2.1 Crea la VM

1. Vai su <https://cloud.oracle.com> → **Compute → Instances → Create Instance**
2. Nome: `smart-crm`
3. **Image**: clicca *Change image* → **Ubuntu 22.04** (Canonical)
4. **Shape**: clicca *Change shape*:
   - Scegli **Ampere** (ARM) → `VM.Standard.A1.Flex`
   - OCPU: **2**, Memory: **12 GB** (sempre gratis fino a 4 OCPU / 24 GB totali)
   - > Oppure **AMD** → `VM.Standard.E2.1.Micro` (1 OCPU, 1 GB) — meno potente
5. **SSH keys**: incolla la tua chiave pubblica (`cat ~/.ssh/id_rsa.pub`)
6. Clicca **Create**

Aspetta ~2 minuti. Prendi nota dell'**IP pubblico** (es. `1.2.3.4`).

### 2.2 Apri le porte nel firewall OCI (Security List)

Il firewall di Oracle è gestito via VCN, **non basta** aprire le porte nell'OS.

1. Vai su **Networking → Virtual Cloud Networks** → clicca la VCN della VM
2. Clicca **Security Lists → Default Security List**
3. Clicca **Add Ingress Rules** e aggiungi:

| Source CIDR  | Protocol | Port range | Descrizione       |
|--------------|----------|------------|-------------------|
| `0.0.0.0/0`  | TCP      | `80`       | HTTP              |
| `0.0.0.0/0`  | TCP      | `443`      | HTTPS (futuro)    |
| `0.0.0.0/0`  | TCP      | `8000`     | Backend (debug)   |

### 2.3 Connettiti alla VM

```bash
ssh ubuntu@1.2.3.4
```

> L'utente predefinito su Ubuntu OCI è `ubuntu`, non `root`.

### 2.4 Apri le porte anche nel firewall OS

Oracle Ubuntu ha anche `iptables` attivo di default — va configurato:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```

### 2.5 Installa Docker e Nginx

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 nginx git iptables-persistent
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
# Riconnettiti via SSH per applicare il gruppo docker
```

### 2.6 Clona il repository

```bash
cd /opt
sudo git clone https://github.com/TUO-USERNAME/smart-crm.git
sudo chown -R ubuntu:ubuntu /opt/smart-crm
cd smart-crm
```

### 2.7 Genera una SECRET\_KEY sicura

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2.8 Crea il file .env

> **Nota ARM**: se hai scelto lo shape Ampere A1, il Docker build compila per `linux/arm64` — funziona senza modifiche, ma la prima build è più lenta.

```bash
nano /opt/smart-crm/.env
```

Incolla questo contenuto (sostituendo i valori):

```
SECRET_KEY=incolla-qui-la-chiave-generata
DJANGO_SECRET_KEY=incolla-qui-la-stessa-chiave
DEBUG=False
ALLOWED_HOSTS=1.2.3.4
DB_HOST=db.XXXXXXXX.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=la-tua-password-supabase
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://smart-crm-virid.vercel.app
ALLOWED_ORIGINS=["https://smart-crm-virid.vercel.app"]
MEDIA_ROOT=/data/media
CSRF_TRUSTED_ORIGINS=http://1.2.3.4
```

> Aggiorna `CORS_ALLOWED_ORIGINS`, `ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS` con i valori definitivi dopo la Fase 3.

### 2.9 Crea il file docker-compose.yml

Il repo dovrebbe già averlo. Se non c'è:

```bash
nano /opt/smart-crm/docker-compose.yml
```

```yaml
services:
  backend:
    build: .
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - media_data:/data/media
    env_file:
      - .env

volumes:
  media_data:
```

### 2.10 Avvia il container

```bash
cd /opt/smart-crm
docker compose up -d --build
```

La prima volta impiega 3-5 minuti. Controlla i log:

```bash
docker compose logs -f
```

Quando vedi `Uvicorn running on http://0.0.0.0:8000` il backend è pronto.

### 2.11 Crea il superuser Django

```bash
docker compose exec -it backend python manage.py createsuperuser
```

### 2.12 Configura Nginx

```bash
sudo nano /etc/nginx/sites-available/smart-crm
```

Incolla:

```nginx
server {
    listen 80;
    server_name 1.2.3.4;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Attiva la config:

```bash
sudo ln -s /etc/nginx/sites-available/smart-crm /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 2.13 Verifica

```bash
curl http://1.2.3.4/health
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

1. Vai su <https://vercel.com> → **Add New Project**
2. Seleziona il repo `smart-crm`
3. **Root Directory**: imposta `frontend`
4. Framework: Vercel rileva automaticamente **Nuxt**
5. Non cliccare ancora Deploy

### 3.3 Imposta le variabili d'ambiente su Vercel

| Nome                   | Valore                    |
| ---------------------- | ------------------------- |
| `NUXT_PUBLIC_API_BASE` | `http://1.2.3.4/api`      |
| `NUXT_PUBLIC_AI_BASE`  | `http://1.2.3.4`          |

### 3.4 Deploy

Clicca **Deploy**. Impiega 2-3 minuti.

Al termine ricevi un URL tipo `https://smart-crm-virid.vercel.app`.

### 3.5 Aggiorna CORS sul VPS con l'URL definitivo

```bash
nano /opt/smart-crm/.env
# aggiorna CORS_ALLOWED_ORIGINS e ALLOWED_ORIGINS con l'URL Vercel
```

Poi riavvia:

```bash
cd /opt/smart-crm && docker compose restart backend
```

---

## FASE 4 — Verifica finale

1. Apri l'URL Vercel nel browser
2. Login con le credenziali del superuser (passo 2.9)
3. Importa un file Excel di test
4. In **Impostazioni** inserisci una API key Anthropic o OpenAI
5. Apri la chat AI e fai una domanda

---

## Aggiornamenti futuri

```bash
# Sulla VM Oracle, ogni volta che aggiorni il codice:
cd /opt/smart-crm
git pull
docker compose up -d --build

# Il frontend (Vercel) si rideploya automaticamente ad ogni git push
```

---

## Problemi comuni

### "relation does not exist" al primo avvio

Le migrazioni non sono girate. Controlla i log:

```bash
docker compose logs backend
```

### CORS error nel browser

L'URL di Vercel non è in `CORS_ALLOWED_ORIGINS`. Aggiorna `.env` e riavvia:

```bash
docker compose restart backend
```

### "No API key configured" nella chat AI

Normale. Ogni utente inserisce la propria chiave Anthropic/OpenAI in Impostazioni.

### Supabase "project paused"

Accade se non usate l'app per 7 giorni (free tier). Vai su Supabase → **Restore project**.

### Aggiornare una variabile d'ambiente

```bash
nano /opt/smart-crm/.env
docker compose restart backend
```

### Vedere i log in tempo reale

```bash
docker compose logs -f backend
```
