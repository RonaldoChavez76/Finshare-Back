from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.user_model import build_user, verify_password, PUBLIC_PROJECTION
from app.utils.jwt_helper import generate_token


class AuthService:

    @staticmethod
    def register(full_name: str, email: str, password: str, phone: str = None) -> dict:
        db = get_db()
        if db.users.find_one({"email": email.lower().strip()}):
            raise ValueError("El email ya está registrado.")

        user_doc = build_user(full_name, email, password, phone)
        db.users.insert_one(user_doc)

        token = generate_token(str(user_doc["_id"]), user_doc["email"])
        user_doc.pop("passwordHash", None)
        return {"user": user_doc, "token": token}

    @staticmethod
    def login(email: str, password: str) -> dict:
        db = get_db()
        user = db.users.find_one({"email": email.lower().strip()})
        if not user or not verify_password(password, user["passwordHash"]):
            raise ValueError("Credenciales inválidas.")
        if not user.get("isActive", True):
            raise ValueError("Cuenta desactivada.")

        token = generate_token(str(user["_id"]), user["email"])
        user.pop("passwordHash", None)
        return {"user": user, "token": token}

    @staticmethod
    def get_profile(user_id: str) -> dict:
        db = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)}, PUBLIC_PROJECTION)
        if not user:
            raise ValueError("Usuario no encontrado.")
        return user

    @staticmethod
    def update_finance_profile(user_id: str, finance_data: dict) -> dict:
        db = get_db()
        finance_data["updatedAt"] = datetime.now(timezone.utc)
        result = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {"finance": finance_data, "updatedAt": datetime.now(timezone.utc)}},
            projection=PUBLIC_PROJECTION,
            return_document=True,
        )
        if not result:
            raise ValueError("Usuario no encontrado.")
        return result

    @staticmethod
    def add_debt(user_id: str, debt_doc: dict) -> dict:
        db = get_db()
        result = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"debts": debt_doc},
                "$set": {"updatedAt": datetime.now(timezone.utc)},
            },
            projection=PUBLIC_PROJECTION,
            return_document=True,
        )
        if not result:
            raise ValueError("Usuario no encontrado.")
        return result
