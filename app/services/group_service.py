from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.grupo_model import build_group, build_member, GrupoModel

class GroupService:
    @staticmethod
    def create_group(owner_id, name, description, group_type):
        db = get_db()
        # Lógica de creación...
        group_doc = build_group(name, owner_id, description, group_type)
        db.groups.insert_one(group_doc)
        return group_doc

    @staticmethod
    def get_all_groups():
        db = get_db()
        return list(db.groups.find())

    # --- ENLACES PARA EL COMPAÑERO (Español) ---
    @staticmethod
    def crear_grupo(datos):
        # Adaptamos el diccionario 'datos' a los argumentos de create_group
        return GroupService.create_group(
            datos.get("ownerId"),
            datos.get("name"),
            datos.get("description", ""),
            datos.get("groupType", "other")
        )

    @staticmethod
    def obtener_todos_los_grupos():
        return GroupService.get_all_groups()

# --- ALIAS DE CLASE (Para que 'GrupoService' también funcione) ---
GrupoService = GroupService