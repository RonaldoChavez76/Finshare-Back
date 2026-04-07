from datetime import datetime, timezone
from bson import ObjectId

# --- Versión de Ale (Funciones) ---
def build_group(name, owner_id, description="", group_type="other"):
    now = datetime.now(timezone.utc)
    return {
        "name": str(name),
        "description": str(description),
        "groupType": str(group_type),
        "ownerId": ObjectId(owner_id),
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
        "members": [
            build_member(owner_id, "Owner", role="admin")
        ],
        "analytics": {
            "stabilityIndex": 100.0,
            "conflictRiskLevel": "low",
            "contributionVariance": 0.0,
            "dominantPayerId": None,
            "calculatedAt": now
        }
    }

def build_member(user_id, display_name, role="member"):
    return {
        "userId": ObjectId(user_id),
        "displayName": str(display_name),
        "role": role,
        "joinedAt": datetime.now(timezone.utc),
        "isActive": True
    }

# --- Versión del Compañero (Clase) ---
class GrupoModel:
    @staticmethod
    def estructura_base(datos):
        # Simplemente llamamos a tu función build_group para no repetir lógica
        return build_group(
            datos.get("name"), 
            datos.get("ownerId"), 
            datos.get("description", ""), 
            datos.get("groupType", "other")
        )

# --- ALIAS PARA PAZ MUNDIAL ---
build_grupo = build_group
build_miembro = build_member