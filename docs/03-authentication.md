# Authentification

## Pourquoi cette approche (et pas better-auth / JWT)

Contexte : un seul utilisateur admin, pas besoin de scalabilité multi-utilisateurs
ni de SSO. Dans ce contexte :

- **Pas de lib d'auth généraliste (better-auth, etc.)** : leur complexité (gestion
  multi-provider, multi-compte) n'apporte rien ici et rend le code plus dur à
  comprendre pour un débutant.
- **Pas de JWT** : un JWT est auto-suffisant et stateless — pratique à grande échelle,
  mais impossible à révoquer instantanément (il reste valide jusqu'à expiration
  même si on veut déconnecter l'utilisateur de force). Une session opaque stockée
  en base, elle, se révoque en supprimant une ligne.

## Vue d'ensemble du flux

```
1. POST /auth/login          (email + mot de passe)
       ↓ si valide
   génère un OTP à 6 chiffres, l'envoie par email, l'enregistre en base
       ↓
2. POST /auth/verify-otp     (email + code reçu)
       ↓ si le code est correct ET non expiré
   crée une session en base + pose un cookie httpOnly dans la réponse
       ↓
3. Toute requête vers une route protégée
   lit le cookie → cherche la session en base → vérifie qu'elle n'est pas expirée
       ↓
4. POST /auth/logout
   supprime la session en base + supprime le cookie
```

## Hash des mots de passe (`app/core/security.py`)

```python
from passlib.context import CryptContext  # ou bcrypt directement, voir note

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Note de compatibilité** : `passlib` (non maintenu depuis 2020) peut planter avec
les versions récentes de `bcrypt` (erreur `module 'bcrypt' has no attribute '__about__'`). Deux solutions :

- Fixer `bcrypt==4.0.1` (compatible avec `passlib`), ou
- Abandonner `passlib` et utiliser `bcrypt` directement :
  ```python
  import bcrypt

  def hash_password(password: str) -> str:
      return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
  ```

**Jamais** utiliser un hash générique (sha256, md5) pour des mots de passe — bcrypt
est volontairement lent, ce qui ralentit les attaques par force brute.

## OTP (`app/core/security.py`)

```python
def generate_otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"  # ex: "042817"

def otp_expiry():
    minutes = int(os.getenv("OTP_DURATION_MINUTES", "3"))
    return utcnow() + timedelta(minutes=minutes)

def send_otp_email(to_email: str, code: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    message = MIMEText(f"Ton code de connexion est : {code}\n\nIl expire dans {os.getenv('OTP_DURATION_MINUTES', '3')} minutes.")
    message["Subject"] = "Code de connexion"
    message["From"] = smtp_user
    message["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()  # chiffre la connexion AVANT d'envoyer les identifiants
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, message.as_string())
```

**Pour envoyer via Gmail** : nécessite un "mot de passe d'application" (pas le
mot de passe du compte) — à générer sur
`https://myaccount.google.com/apppasswords`, après avoir activé la validation
en 2 étapes sur le compte Google.

## Session token (`app/core/security.py`)

```python
def generate_session_token() -> str:
    return secrets.token_urlsafe(32)  # chaîne aléatoire opaque, ~43 caractères

def session_expiry():
    hours = int(os.getenv("SESSION_DURATION_HOURS", "24"))
    return utcnow() + timedelta(hours=hours)
```

## Les routes (`app/routers/auth.py`)

```python
@router.post("/login")
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # même erreur qu'email inconnu ou mdp faux : empêche de deviner
    # si un email existe en base par élimination
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    code = generate_otp_code()
    user.otp_code = code
    user.otp_expires_at = otp_expiry()
    db.commit()

    send_otp_email(user.email, code)
    return {"message": "Code OTP envoyé par email"}


@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest, response: Response, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not user.otp_code:
        raise HTTPException(status_code=401, detail="Aucune demande de connexion en cours")
    if user.otp_code != payload.code:
        raise HTTPException(status_code=401, detail="Code invalide")
    if user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Code expiré")

    # OTP à usage unique : effacé immédiatement après validation
    user.otp_code = None
    user.otp_expires_at = None

    token = generate_session_token()
    session = SessionModel(token=token, user_id=user.id, expires_at=session_expiry())
    db.add(session)
    db.commit()

    response.set_cookie(
        key=os.getenv("SESSION_COOKIE_NAME", "session_token"),
        value=token,
        httponly=True,   # invisible/inaccessible en JavaScript navigateur (anti-XSS)
        secure=True,      # transmis uniquement en HTTPS — mettre False en local HTTP
        samesite="lax",   # protection CSRF de base
        max_age=int(os.getenv("SESSION_DURATION_HOURS", "24")) * 3600,
    )
    return {"message": "Connexion réussie"}


@router.post("/logout")
def logout(response: Response, request: Request, db: DBSession = Depends(get_db)):
    cookie_name = os.getenv("SESSION_COOKIE_NAME", "session_token")
    token = request.cookies.get(cookie_name)
    if token:
        db.query(SessionModel).filter(SessionModel.token == token).delete()
        db.commit()
    response.delete_cookie(cookie_name)
    return {"message": "Déconnecté"}


def get_current_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    cookie_name = os.getenv("SESSION_COOKIE_NAME", "session_token")
    token = request.cookies.get(cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    session = db.query(SessionModel).filter(SessionModel.token == token).first()
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")

    return session.user
```

## Protéger une route

`get_current_user` est une "dependency" FastAPI : l'ajouter à n'importe quelle
route suffit à la protéger.

```python
@router.post("/", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),   # ← ligne qui protège la route
):
    ...
```

Si le cookie est absent ou invalide, FastAPI renvoie `401` **avant** d'exécuter
le corps de la fonction — le code de la route n'a jamais besoin de vérifier
l'authentification lui-même.

## Pourquoi pas de route `POST /users` (création de compte)

Avec un seul utilisateur admin prévu, exposer une route publique de création de
compte serait une faille de sécurité inutile (n'importe qui pourrait tenter de
créer un compte admin). Le compte unique est créé une seule fois via un script
`seed/seed_user.py`, jamais via une route HTTP :

```python
# seed/seed_user.py — lancé une seule fois manuellement, jamais en prod après coup
#  à lancer depuis la racine du projet : python seed/seed_user.py
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
import os
from dotenv import load_dotenv
load_dotenv()

db = SessionLocal()
existing = db.query(User).filter(User.email == "admin@example.com").first()
if not existing:
    user = User(
        email="admin@example.com",
        password=hash_password(os.getenv("ADMIN_INITIAL_PASSWORD")),
        nom="...", prenom="...",
    )
    db.add(user)
    db.commit()
db.close()
```

 Le mot de passe initial doit venir de `.env` (`ADMIN_INITIAL_PASSWORD`),
jamais écrit en clair dans le script lui-même — un mot de passe collé en dur
dans un fichier de code, même local, finit facilement par fuiter (historique
Git, capture d'écran, copier-coller accidentel).

## Changer le mot de passe admin après coup (`seed/update_password.py`)

Script séparé, distinct de `seed_user.py`, à relancer chaque fois qu'un
changement de mot de passe est nécessaire (par exemple si l'ancien a été
exposé accidentellement en clair quelque part) :

```python
# seed/update_password.py — relançable à tout moment
#  à lancer depuis la racine du projet : python seed/update_password.py
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
import os
from dotenv import load_dotenv
load_dotenv()

db = SessionLocal()
user = db.query(User).filter(User.email == "admin@example.com").first()
if user:
    user.password = hash_password(os.getenv("ADMIN_INITIAL_PASSWORD"))
    db.commit()
    print("Mot de passe mis à jour :)")
else:
    print("Aucun utilisateur trouvé avec cet email.")
db.close()
```

Le nouveau mot de passe se met dans `.env` (`ADMIN_INITIAL_PASSWORD`) avant de
lancer le script — jamais écrit en dur dans `update_password.py` lui-même,
pour la même raison que pour `seed_user.py`.

## Points de vigilance avant la mise en production

- [ ] Repasser `secure=True` sur le cookie (utilisé `False` uniquement pour
  tester en HTTP local).
- [ ] Vérifier que `.env` est bien dans `.gitignore` depuis le premier commit.
- [ ] Changer le mot de passe initial s'il a été manipulé en clair pendant le
  développement (collé dans un terminal, un message, etc.).
- [ ] `samesite="strict"` peut être envisagé à la place de `"lax"` si le front
  et l'API sont sur des domaines différents avec des besoins de sécurité
  renforcés — `"lax"` reste correct dans la majorité des cas.
