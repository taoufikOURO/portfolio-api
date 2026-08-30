# Patterns réutilisables sur un autre projet

Ce fichier rassemble les patterns génériques (indépendants du portfolio) à
copier directement sur un nouveau projet FastAPI + SQLAlchemy + Supabase.

## Pattern 1 — Ajouter une nouvelle ressource CRUD, en 4 étapes

Toujours le même ordre, quelle que soit la ressource :

1. **`models/<ressource>.py`** — la table SQLAlchemy.
2. **`schemas/<ressource>.py`** — `<Ressource>Base`, `<Ressource>Create`,
   `<Ressource>Update` (champs `Optional`), `<Ressource>Out` (jamais les
   champs sensibles).
3. **`routers/<ressource>.py`** — GET (public), POST/PUT/DELETE (protégés).
4. Brancher dans `main.py` : `app.include_router(<ressource>_router)`.

### Squelette minimal d'un router CRUD

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.<ressource> import <Ressource>
from app.schemas.<ressource> import <Ressource>Out, <Ressource>Create, <Ressource>Update
from app.routers.auth import get_current_user

router = APIRouter(prefix="/<ressources>", tags=["<ressources>"])


@router.get("/", response_model=list[<Ressource>Out])
def list_items(db: DBSession = Depends(get_db)):
    return db.query(<Ressource>).all()


@router.get("/{item_id}", response_model=<Ressource>Out)
def get_item(item_id: str, db: DBSession = Depends(get_db)):
    item = db.query(<Ressource>).filter(<Ressource>.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    return item


@router.post("/", response_model=<Ressource>Out, status_code=201)
def create_item(
    payload: <Ressource>Create,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = <Ressource>(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=<Ressource>Out)
def update_item(
    item_id: str,
    payload: <Ressource>Update,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = db.query(<Ressource>).filter(<Ressource>.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = db.query(<Ressource>).filter(<Ressource>.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    db.delete(item)
    db.commit()
    return None
```

`exclude_unset=True` est la clé du `PUT` : ne modifie que les champs
réellement envoyés par le client, laisse le reste intact.

## Pattern 2 — Relation many-to-many avec des données à créer/remplacer

Pour une ressource A liée à plusieurs B via une table de jointure (ex: un
article avec plusieurs tags) :

```python
# à la création
db.add(item)
db.flush()  # obtient l'id de `item` sans encore valider la transaction

if payload.related_ids:
    related = db.query(Related).filter(Related.id.in_(payload.related_ids)).all()
    if len(related) != len(payload.related_ids):
        raise HTTPException(status_code=400, detail="Un ou plusieurs éléments liés sont introuvables")
    item.jointure = [Jointure(related_id=r.id, item_id=item.id) for r in related]

db.commit()
```

La vérification `len(related) != len(payload.related_ids)` détecte un ID
inexistant envoyé par erreur — sans elle, l'ID invalide serait silencieusement
ignoré plutôt que de lever une erreur claire.

## Pattern 3 — Upload de fichier intégré à une route CRUD

Voir `04-image-storage.md` pour le détail complet. Le principe général :

```python
@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(
    name: str = Form(...),                    # champs simples en Form
    related_ids: str = Form("[]"),             # listes/objets en JSON stringifié
    file: UploadFile = File(...),              # fichier(s) en File
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    related_id_list = json.loads(related_ids)
    file_url = upload_to_storage(await file.read(), file.filename, "dossier")
    # ... création de l'objet avec file_url ...
```

Cette approche remplace un `<Ressource>Create` Pydantic classique (impossible
avec `multipart/form-data` imbriqué) par des paramètres `Form`/`File`
individuels directement dans la signature de la route.

## Pattern 4 — Réordonnancement en lot (drag & drop)

```python
class ReorderItem(BaseModel):
    id: str
    order: int

class ReorderPayload(BaseModel):
    items: list[ReorderItem]


@router.put("/reorder/batch")
def reorder_items(
    payload: ReorderPayload,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    for item in payload.items:
        db.query(Item).filter(Item.id == item.id).update({"order": item.order})
    db.commit()
    return {"message": "Ordre mis à jour"}
```

Cette route doit être déclarée **avant** `GET /{item_id}` dans le fichier
du router (FastAPI matche les routes dans l'ordre de déclaration — sinon
`"reorder"` est interprété comme une valeur d'`{item_id}`).

## Pattern 5 — Auth par email + mot de passe + OTP + session cookie

Voir `03-authentication.md` pour le détail complet. Applicable tel quel à
n'importe quel projet avec un nombre restreint d'utilisateurs de confiance
(pas pensé pour un système d'inscription publique à grande échelle).

Composants à copier :

- `core/security.py` (hash mdp, génération/vérification OTP, envoi email, token de session)
- `models/user.py` (`User` + `Session`)
- `routers/auth.py` (`/login`, `/verify-otp`, `/logout`, `get_current_user`)
- `seed_user.py` (script de création manuelle du/des comptes)

## Pattern 6 — Import "pour effet de bord" (enregistrement des modèles)

Pour que `Base.metadata.create_all(engine)` connaisse toutes les tables, il
faut que Python ait exécuté chaque fichier de modèle au moins une fois —
même si aucun code n'utilise explicitement le nom importé :

```python
# database/create_tables.py
# à lancer depuis la racine du projet : python database/create_tables.py
from app.core.database import engine, Base
from app.models import user, skill, stack, project, education, experience, article  # noqa: F401

Base.metadata.create_all(engine)
```

Le `# noqa: F401` indique explicitement au linter que l'import "inutilisé"
est volontaire (effet de bord, pas usage direct du nom).

## Pattern 7 — Config centralisée via `.env`, jamais de valeur en dur

Toute valeur sensible ou susceptible de changer entre environnements
(dev/prod) passe par `os.getenv(...)`, avec une valeur par défaut **en
chaîne** (`os.getenv("X", "24")`, pas `os.getenv("X", 24)` — `os.getenv`
attend `str` ou `None` en second argument).

```python
import os
from dotenv import load_dotenv
load_dotenv()

MA_VARIABLE = os.getenv("MA_VARIABLE")
if not MA_VARIABLE:
    raise ValueError("MA_VARIABLE n'est pas définie dans .env")
```

Échouer bruyamment (`raise ValueError`) au démarrage si une variable
obligatoire manque, plutôt que de laisser l'application démarrer dans un état
à moitié configuré qui échouera de façon confuse plus tard.
