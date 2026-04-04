from datetime import datetime
from bson import ObjectId
from app import db 
from app.models.grupo_model import GrupoModel

class GrupoService:
    @staticmethod
    def crear_grupo(datos):
        # 1. Validación de datos mínimos requeridos
        if not datos.get("name"):
            raise ValueError("El nombre del grupo es obligatorio.")
        if not datos.get("ownerId"):
            raise ValueError("El ID del creador (ownerId) es obligatorio.")
            
        # 2. Generar la estructura del documento usando nuestro modelo
        nuevo_grupo = GrupoModel.estructura_base(datos)
        
        # 3. Insertar el documento en la colección 'groups' de MongoDB
        resultado = db.groups.insert_one(nuevo_grupo)
        
        # 4. Retornar el ID del grupo recién creado (convertido a String para JSON)
        return str(resultado.inserted_id)
    
    @staticmethod
    def actualizar_grupo(grupo_id, datos_actualizados):
        # 1. Protegemos campos críticos que no deberían poder editarse
        campos_protegidos = ["_id", "ownerId", "createdAt", "members"]
        for campo in campos_protegidos:
            datos_actualizados.pop(campo, None) # Lo eliminamos del diccionario si intentan enviarlo
            
        if not datos_actualizados:
            raise ValueError("No se enviaron datos válidos para actualizar.")
            
        # 2. Actualizamos la fecha de modificación automáticamente
        datos_actualizados["updatedAt"] = datetime.utcnow()
        
        # 3. Ejecutamos la actualización en MongoDB usando $set
        resultado = db.groups.update_one(
            {"_id": ObjectId(grupo_id)},
            {"$set": datos_actualizados}
        )
        
        # 4. Verificamos si el grupo realmente existía
        if resultado.matched_count == 0:
            raise ValueError("El grupo especificado no existe.")
            
        # Retorna True si se modificó algo, False si enviaron los mismos datos que ya tenía
        return resultado.modified_count > 0
    
    @staticmethod
    def obtener_todos_los_grupos():
        # 1. Buscamos todos los documentos en la colección 'groups'
        grupos_cursor = db.groups.find()
        
        grupos_lista = []
        for grupo in grupos_cursor:
            # 2. Convertimos el _id principal y el ownerId a string
            grupo["_id"] = str(grupo["_id"])
            grupo["ownerId"] = str(grupo["ownerId"])
            
            # 3. Recorremos los miembros para convertir sus IDs también
            for miembro in grupo.get("members", []):
                miembro["userId"] = str(miembro["userId"])
                
            # (Opcional) Si quieres, puedes formatear las fechas aquí, 
            # pero el frontend en React usualmente las puede parsear directo.
            
            grupos_lista.append(grupo)
            
        return grupos_lista
    
    @staticmethod
    def eliminar_grupo(grupo_id):
        # Ejecutamos la eliminación en MongoDB
        resultado = db.groups.delete_one({"_id": ObjectId(grupo_id)})
        
        # Verificamos si realmente se eliminó algo (si el grupo existía)
        if resultado.deleted_count == 0:
            raise ValueError("El grupo especificado no existe o ya fue eliminado.")
            
        # Nota técnica: En una versión más avanzada, aquí podrías agregar:
        # db.shared_expenses.delete_many({"groupId": ObjectId(grupo_id)})
        # para borrar también todos los gastos vinculados a este grupo.
            
        return True