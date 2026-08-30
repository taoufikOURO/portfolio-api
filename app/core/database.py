"""Database connection and session management for FastAPI with SQLAlchemy."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL n'est pas défini dans le fichier .env")

# Le moteur = l'objet qui gère la connexion réelle à Postgres
engine = create_engine(DATABASE_URL)

# SessionLocal = une "fabrique" de sessions de conversation avec la DB
# Chaque requête API ouvrira sa propre session via cette fabrique
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = la classe dont tous nos futurs modèles (User, Project, etc.) vont hériter
Base = declarative_base()


# Fonction utilitaire que FastAPI utilisera pour injecter une session DB
# dans chaque route qui en a besoin, et la refermer proprement après usage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
