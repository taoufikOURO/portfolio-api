import os
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()

existing = db.query(User).filter(User.email == "ourotaoufik1@gmail.com").first()
if existing:
    print("Un utilisateur avec cet email existe déjà, rien fait.")
else:
    user = User(
        email="ourotaoufik1@gmail.com",
        password=hash_password(os.getenv("ADMIN_INITIAL_PASSWORD")),  # change le mot de passe avant de mettre en prod, c'est juste pour le seed
        nom="OURO-BANG'NA",
        prenom="Taoufik",
        titre_professionnel="Data Scientist",
        bio="Étudiant en Master IA & Big Data, je conçois des systèmes qui transforment la donnée brute en décisions concrètes ; du modèle de machine learning à l'interface qui le rend utile.",
        a_propos="Data scientist. Je crée des modèles de machine learning pour répondre à des problèmes concrets, pas pour empiler des techniques à la mode. Ce qui me pousse, c'est de comprendre un problème en profondeur avant de choisir une solution : je préfère creuser une logique jusqu'au bout plutôt que copier une approche toute faite. Je vois la donnée comme un moyen, pas une fin, et un modèle n'a de valeur que s'il devient réellement utilisable par quelqu'un. Rigueur, curiosité, et une exigence assez forte sur ce que je livre : voilà qui je suis, je suis Taoufik OURO-BANG'NA.",
        github="https://github.com/taoufikOURO",
        linkedin="www.linkedin.com/in/taoufik-ouro-bang-na",
        photo="/images/profile/taoufik.jpg",
        cv="https://cvdesignr.com/p/kpa3P1bYNWpLG30?hl=fr_FR",
    )
    db.add(user)
    db.commit()
    print("Utilisateur créé :)")

db.close()
