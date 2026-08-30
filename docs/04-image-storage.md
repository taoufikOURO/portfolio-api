# Stockage d'images (Supabase Storage)

## Pourquoi pas de disque local

Sur la plupart des hébergements modernes (Vercel, et Render sans option payante),
le système de fichiers n'est **pas persistant** : un fichier écrit sur disque à
l'exécution disparaît au prochain redéploiement (ou n'est même pas écrit du tout
sur les plateformes strictement serverless comme Vercel). Il faut donc un service
de stockage externe.

Supabase Storage a été choisi ici parce que la base de données est déjà hébergée
sur Supabase — un seul projet à gérer plutôt que d'ajouter un service tiers
(Cloudinary, S3...) pour un gain marginal.

## Configuration

1. Dashboard Supabase → **Storage** → **New bucket** → cocher **Public bucket**
   (les images d'un portfolio public n'ont pas besoin d'accès restreint).
2. Récupérer dans **Project Settings → API** :
   - `SUPABASE_URL` (l'URL de base du projet, ex: `https://xxxxx.supabase.co`
     — **sans** rien après `.co`, une erreur fréquente est d'y laisser un
     chemin type `/rest/v1`)
   - `SUPABASE_SERVICE_ROLE_KEY` ( jamais la clé `anon` ici — c'est le
     serveur qui uploade en confiance, la `service_role` key ne doit jamais
     transiter vers un navigateur)

## La fonction d'upload (`app/core/storage.py`)

```python
import os
import uuid
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image(file_bytes: bytes, original_filename: str, folder: str) -> str:
    """
    Upload une image vers Supabase Storage et renvoie son URL publique.
    folder : sous-dossier logique dans le bucket, ex "stack", "projets", "profile", "articles"
    """
    extension = original_filename.split(".")[-1]
    unique_name = f"{folder}/{uuid.uuid4()}.{extension}"

    supabase.storage.from_(BUCKET_NAME).upload(
        path=unique_name,
        file=file_bytes,
        file_options={"content-type": f"image/{extension}"},
    )

    return supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
```

**Pourquoi un nom de fichier généré (`uuid.uuid4()`)** : évite toute collision si
deux images sont uploadées avec le même nom d'origine (`logo.png` uploadé deux
fois n'écrase pas la première version).

## Pattern retenu : upload intégré aux routes, pas de route séparée

Deux approches étaient possibles :

- **Route d'upload séparée** (`POST /uploads/image`) qui renvoie une URL, à
  utiliser ensuite dans un second appel `POST /projects/` avec cette URL.
- **Upload intégré directement dans la route de création/modification** : un
  seul appel réseau, le fichier ET les autres champs arrivent ensemble.

**Le second pattern a été retenu** : il évite un aller-retour réseau inutile
côté client. La route reçoit alors un `multipart/form-data` plutôt qu'un JSON
pur, ce qui change légèrement la signature de la route.

### Exemple concret (route de création d'un `Project`)

```python
@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    name: str = Form(...),
    description: str = Form(...),
    app_link: Optional[str] = Form(None),
    github_link: Optional[str] = Form(None),
    order: int = Form(0),
    stack_ids: str = Form("[]"),        # JSON stringifié : '["id1", "id2"]'
    contributors: str = Form("[]"),     # JSON stringifié : '[{"name": "...", "github_url": "..."}]'
    image: UploadFile = File(...),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stack_id_list = json.loads(stack_ids)
    contributors_list = json.loads(contributors)

    picture_url = upload_image(await image.read(), image.filename, "projets")

    project = Project(
        name=name, description=description, app_link=app_link,
        github_link=github_link, picture=picture_url, order=order,
    )
    db.add(project)
    db.flush()
    # ... création des relations stack_ids / contributors ...
    db.commit()
    db.refresh(project)
    return project
```

**Ce que le front doit envoyer** : un `FormData` (pas un `JSON.stringify` global) —
les champs simples en texte, les listes/objets complexes en `JSON.stringify(...)`
dans un champ texte, et le fichier image comme fichier binaire dans le même
`FormData`.

```js
const formData = new FormData();
formData.append("name", "Mon projet");
formData.append("description", "...");
formData.append("stack_ids", JSON.stringify(["id-1", "id-2"]));
formData.append("contributors", JSON.stringify([{ name: "...", github_url: "..." }]));
formData.append("image", fileInput.files[0]);

fetch("/projects/", { method: "POST", body: formData, credentials: "include" });
```

`credentials: "include"` est nécessaire pour que le cookie de session soit
transmis avec la requête.

## À la modification : image optionnelle

Sur les routes `PUT`, le champ image est optionnel (`Optional[UploadFile] = File(None)`) — on ne remplace l'image existante que si une nouvelle est
effectivement fournie :

```python
if image is not None:
    project.picture = upload_image(await image.read(), image.filename, "projets")
```

## Ressources concernées par un upload d'image dans ce projet

| Ressource         | Champ           | Obligatoire à la création ?  |
| ----------------- | --------------- | ------------------------------ |
| `Project`       | `picture`     | Oui                            |
| `Stack`         | `picture`     | Oui                            |
| `User` (profil) | `photo`       | N/A — modification uniquement |
| `Article`       | `cover_image` | Non (optionnel)                |
