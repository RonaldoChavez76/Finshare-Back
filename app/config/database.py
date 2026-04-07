from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from app.config.settings import active_config

_client: MongoClient = None
_db: Database = None


def get_db() -> Database:
    global _client, _db
    if _db is None:
        _client = MongoClient(active_config.MONGO_URI)
        _db = _client[active_config.MONGO_DB_NAME]
        _ensure_indexes(_db)
    return _db


def _ensure_indexes(db: Database):
    """Crea todos los índices necesarios al iniciar la app."""
    # users
    db.users.create_index("email", unique=True)

    # groups
    db.groups.create_index("ownerId")
    db.groups.create_index("members.userId")

    # shared_expenses
    db.shared_expenses.create_index(
        [("groupId", ASCENDING), ("expenseDate", ASCENDING)]
    )
    db.shared_expenses.create_index("paidBy")

    # simulations
    db.simulations.create_index("createdBy")
    db.simulations.create_index("targetGroupId")
