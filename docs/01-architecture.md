# Architecture générale

## Structure des dossiers

```
portfolio-api/
├── app/
│   ├── main.py                # point d'entrée, branche tous les routers
│   ├── core/                  # code transverse, sans logique métier propre à une ressource
│   │   ├── database.py        # connexion SQLAlchemy, session, Base
│   │   ├── security.py        # hash mdp, OTP, envoi email, tokens de session
│   │   ├── storage.py         # upload vers Supabase Storage
│   │   └── utils.py           # generate_uuid, generate_slug, utcnow
│   ├── models/                # un fichier par table/domaine (SQLAlchemy)
│   │   ├── user.py            # User, Session
│   │   ├── skill.py           # Skill
│   │   ├── stack.py           # Stack
│   │   ├── project.py         # Project, ProjectContributor, ProjectStack
│   │   ├── education.py       # Education, SkillOnEducation
│   │   ├── experience.py      # Experience, ExperienceSkill
│   │   └── article.py         # Article
│   ├── schemas/                # un fichier par domaine (Pydantic — validation/sérialisation)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── skill.py
│   │   ├── stack.py
│   │   ├── project.py
│   │   ├── education.py
│   │   ├── experience.py
│   │   └── article.py
│   └── routers/                # un fichier par domaine (routes FastAPI)
│       ├── auth.py
│       ├── users.py
│       ├── skills.py
│       ├── stacks.py
│       ├── projects.py
│       ├── education.py
│       ├── experience.py
│       └── articles.py
├── database/
│   └── create_tables.py        # script à lancer une fois : crée les tables en base
├── seed/
│   ├── seed_user.py            # script à lancer une fois : crée le compte admin unique
│   └── update_password.py      # script à relancer au besoin : change le mot de passe admin
├── .env                        # variables d'environnement (jamais commité)
└── .gitignore
```

**Pourquoi ces scripts sont sortis de la racine** : ce sont des scripts d'exploitation
(setup initial, maintenance), pas du code applicatif servi par l'API — les
regrouper dans `database/` et `seed/` évite qu'ils se mélangent visuellement avec
`app/` (le vrai code de l'application) à la racine du projet.

**Point d'attention pour ces scripts** : ils font tous des imports du type
`from app.core.database import ...` — comme ils ne sont plus à la racine, ils
doivent être lancés **depuis la racine du projet** (pas depuis `database/` ou
`seed/` eux-mêmes), sinon Python ne retrouve pas le package `app` :

```bash
# depuis la racine du projet, correct :
python database/create_tables.py
python seed/seed_user.py

# depuis l'intérieur du dossier, incorrect (ModuleNotFoundError: No module named 'app') :
cd seed && python seed_user.py
```

## Pourquoi cette séparation en 4 couches (core / models / schemas / routers)

Chaque couche a une responsabilité unique, ce qui permet de localiser immédiatement
où intervenir pour un changement donné :

- **`core/`** : rien de spécifique à une ressource métier. Si tu ajoutes une nouvelle
  table demain, tu ne touches jamais à `core/`.
- **`models/`** : décrit la structure des tables en base (SQLAlchemy). Une classe = une table.
- **`schemas/`** : décrit ce qu'un client peut envoyer/recevoir en JSON (Pydantic).
  Volontairement séparé des `models/` : un modèle DB a des champs qu'on ne veut
  jamais exposer (mot de passe, OTP), la séparation empêche les fuites accidentelles.
- **`routers/`** : la logique HTTP elle-même (routes, codes de statut, dépendances).

## Pourquoi chaque domaine a 3 fichiers séparés (model + schema + router)

Pour ajouter une nouvelle ressource "Testimonial" par exemple :

1. `models/testimonial.py` — la table.
2. `schemas/testimonial.py` — ce qui rentre/sort en JSON.
3. `routers/testimonial.py` — les routes.
4. Brancher le router dans `main.py`.

Toujours les mêmes 4 étapes, dans le même ordre, quelle que soit la ressource.

## Dépendances principales

```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
python-dotenv
bcrypt              # hash des mots de passe (voir 03-authentication.md)
pydantic[email]     # pour le type EmailStr
supabase            # SDK Python pour Supabase Storage
python-multipart    # requis par FastAPI pour les UploadFile / Form
```

Génère un `requirements.txt` figé avec :

```bash
pip freeze > requirements.txt
```

## Variables d'environnement (`.env`)

```dotenv
# Base de données (Supabase Postgres)
DATABASE_URL="postgresql://postgres.xxxxx:motdepasse@aws-0-xxx.pooler.supabase.com:6543/postgres?pgbouncer=true"
DIRECT_URL="postgresql://postgres.xxxxx:motdepasse@aws-0-xxx.pooler.supabase.com:5432/postgres"

# Supabase Storage
SUPABASE_URL="https://xxxxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="..."
SUPABASE_STORAGE_BUCKET="portfolio-images"

# Envoi d'email (OTP)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="tonemail@gmail.com"
SMTP_PASSWORD="mot_de_passe_application_16_caracteres"

# Session / OTP
SESSION_COOKIE_NAME="session_token"
SESSION_DURATION_HOURS=24
OTP_DURATION_MINUTES=3

# Utilisé uniquement par seed_user.py, jamais lu par l'app elle-même
ADMIN_INITIAL_PASSWORD="mot_de_passe_du_premier_compte"
```

Aucune de ces valeurs ne doit jamais être codée en dur dans le code source,
ni committée dans Git — `.env` doit figurer dans `.gitignore` dès le premier commit
du projet.
