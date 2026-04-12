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
    
    @staticmethod
    def get_user_groups(user_id):
        db = get_db()
        
        # Buscamos en MongoDB: Trae los grupos donde soy el creador (ownerId)
        # o donde mi ID está dentro de la lista de integrantes (members.userId)
        cursor = db.groups.find({
            "$or": [
                {"ownerId": ObjectId(user_id)},
                {"members.userId": ObjectId(user_id)}
            ]
        })
        
        # Formateamos la lista limpiando los ObjectIds para que Flask los pueda hacer JSON
        grupos_lista = []
        for grupo in cursor:
            grupo["_id"] = str(grupo["_id"])
            grupo["ownerId"] = str(grupo["ownerId"])
            
            for miembro in grupo.get("members", []):
                miembro["userId"] = str(miembro["userId"])
                
            grupos_lista.append(grupo)
            
        return grupos_lista
    
    
    @staticmethod
    def update_group(group_id, data):
        db = get_db()
        
        # 1. Protegemos los campos críticos para que nadie los pueda hackear/modificar
        campos_protegidos = ["_id", "ownerId", "createdAt", "members"]
        for campo in campos_protegidos:
            data.pop(campo, None)
            
        if not data:
            return False
            
        # 2. Actualizamos la fecha de modificación automáticamente
        data["updatedAt"] = datetime.now(timezone.utc)
        
        # 3. Guardamos en MongoDB
        result = db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": data}
        )
        
        # Retorna True si realmente se modificó algo
        return result.modified_count > 0

    @staticmethod
    def delete_group(group_id):
        db = get_db()
        
        # 1. Eliminamos el grupo de MongoDB
        result = db.groups.delete_one({"_id": ObjectId(group_id)})
        
        if result.deleted_count == 0:
            raise ValueError("El grupo no existe o ya fue eliminado.")
            
        return True
    
    @staticmethod
    def get_group(group_id, user_id):
        db = get_db()
        
        # Buscamos el grupo, pero por seguridad exigimos que el usuario
        # que hace la petición sea el creador o un miembro del grupo
        grupo = db.groups.find_one({
            "_id": ObjectId(group_id),
            "$or": [
                {"ownerId": ObjectId(user_id)},
                {"members.userId": ObjectId(user_id)}
            ]
        })
        
        if not grupo:
            raise ValueError("El grupo no existe o no tienes permiso para verlo.")
            
        # Limpiamos los ObjectIds para poder enviarlo como JSON a React
        grupo["_id"] = str(grupo["_id"])
        grupo["ownerId"] = str(grupo["ownerId"])
        
        for miembro in grupo.get("members", []):
            miembro["userId"] = str(miembro["userId"])
            
        return grupo
    
    
    @staticmethod
    def add_member(group_id, email):
        db = get_db()
        
        # 1. Buscamos al usuario por su correo
        user_to_add = db.users.find_one({"email": email})
        if not user_to_add:
            raise ValueError("No se encontró ningún usuario con ese correo electrónico.")

        # 2. Verificamos si ya es miembro para no duplicarlo
        already_member = db.groups.find_one({
            "_id": ObjectId(group_id),
            "members.userId": user_to_add["_id"]
        })
        if already_member:
            raise ValueError("Este usuario ya forma parte del grupo.")

        # 3. Creamos el nuevo objeto miembro
        nuevo_miembro = {
            "userId": user_to_add["_id"],
            "displayName": user_to_add.get("fullName", "Usuario"),
            "role": "member",
            "joinedAt": datetime.now(timezone.utc),
            "isActive": True
        }

        # 4. Lo empujamos ($push) al arreglo de members en MongoDB
        db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$push": {"members": nuevo_miembro}}
        )
        
        # IMPORTANTE: Convertir IDs a string antes de devolver al Controller
        nuevo_miembro["userId"] = str(nuevo_miembro["userId"])
        return nuevo_miembro

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
    
    @staticmethod
    def remove_member(group_id, requester_id, user_id_to_remove):
        db = get_db()
        
        # 1. Verificar si el grupo existe y obtener información
        group = db.groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ValueError("El grupo no existe.")

        # 2. SEGURIDAD: Solo el dueño (ownerId) puede eliminar miembros
        if str(group["ownerId"]) != requester_id:
            raise PermissionError("Solo el administrador del grupo puede eliminar miembros.")

        # 3. Evitar que el dueño se elimine a sí mismo desde aquí
        if str(group["ownerId"]) == user_id_to_remove:
            raise ValueError("No puedes eliminar al dueño del grupo. Debes eliminar el grupo completo.")

        # 4. Usamos $pull para sacar al usuario del arreglo de members en MongoDB
        result = db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$pull": {"members": {"userId": ObjectId(user_id_to_remove)}}}
        )

        if result.modified_count == 0:
            raise ValueError("El usuario no pertenece a este grupo.")

        # Devolvemos el grupo actualizado
        return GroupService.get_group(group_id, requester_id)

    @staticmethod
    def get_member_breakdown(group_id, requester_id):
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ValueError("Grupo no encontrado")
        
        # Verificar que el solicitante sea miembro
        is_member = any(str(m["userId"]) == requester_id for m in group.get("members", []))
        if not is_member and str(group.get("ownerId")) != requester_id:
             raise PermissionError("No tienes permiso para ver este desglose")

        # Traer todos los gastos del grupo
        gastos = list(db.shared_expenses.find({"groupId": ObjectId(group_id)}))
        members = group.get("members", [])
        member_names = {str(m["userId"]): m.get("displayName", "Usuario") for m in members}

        # Calcular deudas netas entre pares
        # Estructura: debts[deudor][acreedor] = monto
        debts = {}

        for g in gastos:
            paid_by_id = str(g["paidBy"])
            for s in g.get("splits", []):
                u_id = str(s["userId"])
                if u_id == paid_by_id:
                    continue
                
                amount_pending = float(s.get("amountOwed", 0)) - float(s.get("amountPaid", 0))
                if amount_pending > 0:
                    if u_id not in debts: debts[u_id] = {}
                    debts[u_id][paid_by_id] = debts[u_id].get(paid_by_id, 0) + amount_pending

        # Simplificar (netear) deudas si A le debe a B y B le debe a A
        breakdown = []
        for deudor, acreedores in debts.items():
            for acreedor, monto in acreedores.items():
                breakdown.append({
                    "fromId": deudor,
                    "fromName": member_names.get(deudor, "Usuario"),
                    "toId": acreedor,
                    "toName": member_names.get(acreedor, "Usuario"),
                    "amount": round(monto, 2)
                })

        return breakdown

# --- ALIAS DE CLASE (Para que 'GrupoService' también funcione) ---
GrupoService = GroupService