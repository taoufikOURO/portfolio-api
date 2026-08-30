"""Script to create the database tables."""

from app.core.database import engine, Base
from app.routers import (
    experience,
    education,
    projects,
    skills,
    stacks,
    users,
)  # essentiel

print("Création des tables en cours...")
Base.metadata.create_all(engine)
print("Tables créées avec succès :)")
