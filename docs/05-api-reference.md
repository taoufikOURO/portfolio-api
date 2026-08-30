# Référence API

Toutes les routes sont aussi consultables et testables interactivement sur
`/docs` (Swagger, généré automatiquement par FastAPI).

Légende :  route publique ·  route protégée (nécessite le cookie de session)

## Auth

###  `POST /auth/login`

```json
// body
{ "email": "admin@example.com", "password": "..." }
// réponse 200
{ "message": "Code OTP envoyé par email" }
// réponse 401 si identifiants invalides
```

###  `POST /auth/verify-otp`

```json
// body
{ "email": "admin@example.com", "code": "042817" }
// réponse 200 + pose un cookie httpOnly `session_token`
{ "message": "Connexion réussie" }
// réponse 401 si code invalide ou expiré
```

###  `POST /auth/logout`

Supprime la session en base et le cookie. Réponse 200.

## Profil (`User`)

###  `GET /profile/`

Renvoie le profil public (jamais le mot de passe ni les champs OTP).

```json
{
  "id": "...", "email": "...", "nom": "...", "prenom": "...",
  "titre_professionnel": "...", "bio": "...", "a_propos": "...",
  "github": "...", "linkedin": "...", "photo": "...", "cv": "..."
}
```

###  `PUT /profile/` — `multipart/form-data`

Champs `Form` (tous optionnels) : `nom`, `prenom`, `titre_professionnel`, `bio`,
`a_propos`, `github`, `linkedin`, `cv`. Champ fichier optionnel : `photo`.

Email et mot de passe volontairement non modifiables ici — nécessiteraient une
route dédiée avec re-vérification.

## Compétences (`Skill`)

- `GET /skills/`  — liste toutes les compétences.
- `POST /skills/`  — body JSON `{ "name": "Python" }`.
- `PUT /skills/{id}`  — body JSON `{ "name": "..." }`.
- `DELETE /skills/{id}`  — 204.

## Technologies (`Stack`)

- `GET /stacks/`  — triée par `order` croissant.
- `GET /stacks/{id}` 
- `POST /stacks/`  — `multipart/form-data` : `name` (Form), `order` (Form,
  défaut 0), `image` (File, obligatoire).
- `PUT /stacks/{id}`  — mêmes champs, tous optionnels, `image` optionnelle.
- `DELETE /stacks/{id}` 
- `PUT /stacks/reorder/batch`  — voir section Réordonnancement plus bas.

## Projets (`Project`)

- `GET /projects/`  — triée par `order` croissant, inclut `stacks` et
  `contributors` dans la réponse.
- `GET /projects/{id}` 
- `POST /projects/`  — `multipart/form-data` :
  - `name`, `description` (Form, obligatoires)
  - `app_link`, `github_link` (Form, optionnels)
  - `order` (Form, défaut 0)
  - `stack_ids` (Form, JSON stringifié, ex `'["id1","id2"]'`, défaut `"[]"`)
  - `contributors` (Form, JSON stringifié, ex `'[{"name":"...","github_url":"..."}]'`, défaut `"[]"`)
  - `image` (File, obligatoire)
- `PUT /projects/{id}`  — mêmes champs, tous optionnels.
- `DELETE /projects/{id}` 
- `PUT /projects/reorder/batch` 

## Formations (`Education`)

- `GET /education/`  — triée par `start_date` décroissant, inclut `skills`.
- `GET /education/{id}` 
- `POST /education/`  — body JSON :
  ```json
  {
    "title": "...", "description": "...",
    "start_date": "2023-09-01T00:00:00Z", "end_date": null,
    "school_name": "...", "school_address": "...", "average": 15.5,
    "skill_ids": ["id-1", "id-2"]
  }
  ```
- `PUT /education/{id}`  — mêmes champs, tous optionnels.
- `DELETE /education/{id}` 

## Expériences (`Experience`)

Même structure qu'`Education`, avec `company_name`/`company_address` au lieu
de `school_name`/`school_address`, pas de champ `average`.

- `GET /experience/` 
- `GET /experience/{id}` 
- `POST /experience/` 
- `PUT /experience/{id}` 
- `DELETE /experience/{id}` 

## Articles (`Article`)

- `GET /articles/?published_only=true`  — `published_only` (bool, défaut
  `true`) : passer `false` pour voir aussi les brouillons (usage admin).
- `GET /articles/{slug}` 
- `POST /articles/upload`  — `multipart/form-data` :
  - `title`, `excerpt` (Form, obligatoires)
  - `published` (Form bool, défaut `false`)
  - `file` (File, obligatoire, doit se terminer par `.md`) — son **contenu
    texte** est extrait et stocké tel quel dans `content` (Markdown brut,
    rendu en HTML côté front au moment de l'affichage)
  - `cover_image` (File, optionnel)
- `PUT /articles/{id}`  — mêmes champs, tous optionnels ; permet aussi de
  remplacer le fichier `.md` (`file`) et/ou l'image de couverture.
- `DELETE /articles/{id}` 

`slug` n'est jamais fourni par le client — généré automatiquement côté serveur
(32 caractères hexadécimaux aléatoires).

## Réordonnancement (drag & drop)

Concerne `Project` et `Stack`. Le glisser-déposer visuel se fait côté front
(librairie type `@dnd-kit`) ; l'API se contente d'enregistrer le résultat final.

```
PUT /projects/reorder/batch   
PUT /stacks/reorder/batch     
```

```json
// body, dans les deux cas — la liste complète des éléments avec leur nouvelle position
{
  "items": [
    { "id": "id-1", "order": 0 },
    { "id": "id-2", "order": 1 },
    { "id": "id-3", "order": 2 }
  ]
}
```

Réponse 200 : `{ "message": "Ordre mis à jour" }`.

Ces routes doivent être déclarées **avant** la route `GET /{id}` équivalente
dans le fichier du router, sinon FastAPI tente d'interpréter `"reorder"` comme
une valeur d'`{id}`.
