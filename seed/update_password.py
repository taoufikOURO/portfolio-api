from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
import os
from dotenv import load_dotenv

load_dotenv()

db = SessionLocal()
user = db.query(User).filter(User.email == "ourotaoufik1@gmail.com").first()
user.password = hash_password(os.getenv("ADMIN_INITIAL_PASSWORD"))
db.commit()
db.close()
print("Mot de passe mis à jour :)")
