# Plateforme e-Parti — République Démocratique du Congo
# Gestion des adhésions, membres, cartes, finances et campagnes.

## Démarrage rapide

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
# Copier .env.example → .env (DATABASE_URL PostgreSQL)
python manage.py migrate
python manage.py seed_rdc
python manage.py runserver
```

- Accueil : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/ (`admin` / `admin123`)
- API JWT : `POST /api/auth/token/`
- Base : PostgreSQL (`e-Parti`, user `postgres`)

## Apps

| App | Rôle |
|-----|------|
| `accounts` | Utilisateur custom + rôles |
| `territoires` | Province → Ville → Commune → Section |
| `membership` | Adhésions, membres, cartes PDF/QR |
| `finances` | Cotisations + export Excel |
| `organisation` | Événements & affectations |
| `api` | DRF + JWT |
| `core` | Dashboard, logs, notifications |

## Production

1. Copier `.env.example` → `.env`
2. Définir `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`
3. `DATABASE_URL=postgres://postgres:123456@127.0.0.1:5432/e-Parti`
4. `gunicorn eparti.wsgi:application`
5. Celery (optionnel) : `celery -A eparti worker -l info`

## Génération carte

`generate_membership_card(membre)` dans `membership/services/carte.py` :
- QR (nom, N° membre, URL vérification)
- PDF format PVC CR80
- Numéro d'ordre `000001`
