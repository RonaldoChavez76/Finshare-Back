"""
Script de inicialización de MongoDB para FinShare Analytics.
Uso: python scripts/setup_db.py

Crea colecciones, índices y un usuario de prueba.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import MongoClient, ASCENDING
from app.config.settings import active_config
from app.models.user_model import build_user
from app.models.grupo_model import build_group, build_member
from bson import ObjectId

client = MongoClient(active_config.MONGO_URI)
db     = client[active_config.MONGO_DB_NAME]


def create_indexes():
    print("📌 Creando índices...")

    db.users.create_index("email", unique=True)
    print("  ✅ users.email (unique)")

    db.groups.create_index("ownerId")
    db.groups.create_index("members.userId")
    print("  ✅ groups.ownerId / groups.members.userId")

    db.shared_expenses.create_index(
        [("groupId", ASCENDING), ("expenseDate", ASCENDING)]
    )
    db.shared_expenses.create_index("paidBy")
    print("  ✅ shared_expenses compound + paidBy")

    db.simulations.create_index("createdBy")
    db.simulations.create_index("targetGroupId")
    print("  ✅ simulations.createdBy / simulations.targetGroupId")

    db.transactions.create_index([("userId", ASCENDING), ("transactionDate", ASCENDING)])
    db.transactions.create_index([("userId", ASCENDING), ("type", ASCENDING)])
    print("  ✅ transactions.userId compound")


def seed_data():
    print("\n🌱 Insertando datos de prueba...")

    # Limpiar colecciones de prueba si existen
    if active_config.MONGO_DB_NAME.endswith("_dev") or active_config.MONGO_DB_NAME.endswith("_test"):
        for col in ["users", "groups", "shared_expenses", "transactions"]:
            db[col].delete_many({})
        print("  🗑  Colecciones limpiadas (entorno dev/test)")

    # Usuario 1 - Owner
    user1 = build_user("Ana García", "ana@finshare.mx", "Password1")
    db.users.insert_one(user1)
    print(f"  👤 Usuario creado: ana@finshare.mx  (id: {user1['_id']})")

    # Usuario 2 - Miembro
    user2 = build_user("Luis Pérez", "luis@finshare.mx", "Password1")
    db.users.insert_one(user2)
    print(f"  👤 Usuario creado: luis@finshare.mx (id: {user2['_id']})")

    # Grupo
    group = build_group(
        name="Depa Tlalpan",
        owner_id=user1["_id"],
        description="Gastos del departamento compartido",
        group_type="roommates",
    )
    group["members"][0]["displayName"] = user1["fullName"]
    group["members"].append(
        build_member(user2["_id"], user2["fullName"], role="member")
    )
    db.groups.insert_one(group)
    print(f"  🏠 Grupo creado: '{group['name']}' (id: {group['_id']})")

    print("\n✅ Setup completado.")
    print(f"   DB: {active_config.MONGO_DB_NAME}")
    print(f"   URI: {active_config.MONGO_URI}")


if __name__ == "__main__":
    create_indexes()
    seed_data()
    client.close()
