# Documentation technique — Portfolio API

API backend FastAPI pour un portfolio personnel : CRUD complet, authentification
par email + mot de passe + OTP, upload d'images vers Supabase Storage.

Cette documentation est écrite pour être réutilisable telle quelle sur d'autres
projets similaires, pas seulement comme référence de ce projet précis.

## Sommaire

1. [Architecture générale](./01-architecture.md) : stack technique, structure des dossiers
2. [Schéma de base de données](./02-database-schema.md) : tous les modèles et leurs relations
3. [Authentification](./03-authentication.md) : flux login + OTP + session cookie, en détail
4. [Stockage d&#39;images](./04-image-storage.md) : pattern d'upload vers Supabase Storage
5. [Référence API](./05-api-reference.md) : toutes les routes avec exemples de requêtes/réponses
6. [Patterns réutilisables](./06-patterns-reutilisables.md) : les patterns génériques à copier sur un autre projet

## Stack technique

| Composant         | Choix                                      | Pourquoi                                                                         |
| ----------------- | ------------------------------------------ | -------------------------------------------------------------------------------- |
| Framework API     | FastAPI                                    | Typage fort, doc auto-générée (`/docs`), async natif                        |
| ORM               | SQLAlchemy (classique, pas d'Alembic)      | Contrôle explicite, pas de couche magique                                       |
| Base de données  | PostgreSQL, hébergée sur Supabase        | Gratuit pour un petit projet, interface d'admin incluse                          |
| Authentification  | Maison (pas de lib type better-auth)       | Un seul utilisateur admin, la complexité d'une lib généraliste n'apporte rien |
| Sessions          | Cookie httpOnly + table`Session` en base | Révocable instantanément, pas de JWT stateless                                 |
| Stockage fichiers | Supabase Storage                           | Cohérent avec la DB (même projet), survit aux redéploiements Render           |
| Hébergement API  | Render                                     | Déploiement simple depuis Git                                                   |

## Démarrage rapide (pour un nouveau développeur qui reprend ce projet)

```bash
git clone <repo>
cd portfolio-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # ou la liste de paquets de 01-architecture.md
cp .env.example .env                   # puis remplir les vraies valeurs
python database/create_tables.py       # crée les tables en base (une seule fois)
python seed/seed_user.py               # crée le compte admin (une seule fois)
uvicorn app.main:app --reload
```

Puis ouvrir `http://localhost:8000/docs` pour la documentation interactive Swagger.

## Décisions volontairement non standards (et pourquoi)

Ce projet s'écarte de certaines pratiques "par défaut" en connaissance de cause :

- **Pas d'Alembic** : schéma stable, projet solo, `Base.metadata.create_all()` suffit.
  À reconsidérer si le schéma doit évoluer souvent une fois en prod avec des données réelles.
- **Pas de JWT** : un seul utilisateur, pas besoin de scalabilité stateless. Le cookie
  de session + table `Session` permet une révocation immédiate, plus simple à raisonner.
- **Upload d'image intégré aux routes de création/modification**, plutôt qu'une route
  d'upload séparée : évite un aller-retour réseau supplémentaire côté client.
