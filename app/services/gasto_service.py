from datetime import datetime

from app import db
from app.models.gasto_compartido_model import GastoCompartidoModel
from bson.objectid import ObjectId

class GastoService:
    @staticmethod
    def crear_gasto_con_division(datos):
        # Extraemos los datos clave
        grupo_id = datos.get("groupId")
        monto_total = float(datos.get("totalAmount"))
        pagado_por = datos.get("paidBy") # El ID de quien pagó todo
        
        # 1. Buscamos el grupo en MongoDB para ver a los miembros
        grupo = db.groups.find_one({"_id": ObjectId(grupo_id)})
        if not grupo:
            raise ValueError("El grupo especificado no existe.")
            
        miembros = grupo.get("members", [])
        cantidad_miembros = len(miembros)
        
        if cantidad_miembros == 0:
            raise ValueError("El grupo no tiene miembros para dividir el gasto.")
            
        # 2. EL ALGORITMO: División equilibrada
        monto_por_persona = round(monto_total / cantidad_miembros, 2)
        splits_calculados = []
        
        for miembro in miembros:
            usuario_id_str = str(miembro.get("userId"))
            es_pagador = (usuario_id_str == pagado_por)
            
            # Construimos el estado de deuda de cada integrante
            split = {
                "userId": miembro.get("userId"),
                "userName": miembro.get("displayName"),
                # El que pagó no se debe a sí mismo, los demás sí deben su parte
                "amountOwed": 0 if es_pagador else monto_por_persona,
                "amountPaid": monto_total if es_pagador else 0,
                "status": "settled" if es_pagador else "pending",
                "settledAt": None
            }
            splits_calculados.append(split)
            
        # 3. Pedimos la estructura al modelo y lo guardamos
        nuevo_gasto = GastoCompartidoModel.estructura_base(datos, splits_calculados)
        resultado = db.shared_expenses.insert_one(nuevo_gasto)
        
        return str(resultado.inserted_id)
    
    @staticmethod
    def obtener_saldos_grupo(grupo_id):
        # 1. Traemos todos los gastos que pertenezcan a este grupo
        gastos = db.shared_expenses.find({"groupId": ObjectId(grupo_id)})
        
        # 2. Diccionario temporal para ir sumando los saldos de cada integrante
        saldos = {}
        
        for gasto in gastos:
            for split in gasto.get("splits", []):
                user_id_str = str(split["userId"])
                user_name = split.get("userName", "Desconocido")
                
                # Si es la primera vez que vemos a este usuario en el ciclo, lo inicializamos en 0
                if user_id_str not in saldos:
                    saldos[user_id_str] = {
                        "userId": user_id_str,
                        "userName": user_name,
                        "totalPagado": 0.0,
                        "totalAdeudado": 0.0,
                        "balanceNeto": 0.0
                    }
                
                # Sumamos lo que pagó y lo que debe en este gasto en particular
                saldos[user_id_str]["totalPagado"] += float(split.get("amountPaid", 0))
                saldos[user_id_str]["totalAdeudado"] += float(split.get("amountOwed", 0))
        
        # 3. Calculamos el balance neto final
        resultados = []
        for user_id, data in saldos.items():
            # Balance Neto = Lo que pagué - Lo que me tocaba pagar
            data["balanceNeto"] = round(data["totalPagado"] - data["totalAdeudado"], 2)
            resultados.append(data)
            
        return resultados
    
    
    @staticmethod
    def actualizar_gasto(gasto_id, datos_actualizados):
        # 1. Limpiamos campos que el usuario no debería poder alterar manualmente
        campos_protegidos = ["_id", "groupId", "createdAt", "splits"]
        for campo in campos_protegidos:
            datos_actualizados.pop(campo, None)
            
        if not datos_actualizados:
            raise ValueError("No se enviaron datos válidos para actualizar.")

        # 2. Buscamos el gasto actual en la base de datos
        gasto_actual = db.shared_expenses.find_one({"_id": ObjectId(gasto_id)})
        if not gasto_actual:
            raise ValueError("El gasto especificado no existe.")

        # 3. VERIFICACIÓN CRÍTICA: ¿Necesitamos recalcular el dinero?
        recalcular_splits = False
        if "totalAmount" in datos_actualizados or "paidBy" in datos_actualizados:
            recalcular_splits = True

        # Tomamos los valores nuevos si vienen, o mantenemos los viejos si no se modificaron
        nuevo_total = float(datos_actualizados.get("totalAmount", gasto_actual.get("totalAmount")))
        nuevo_pagador = str(datos_actualizados.get("paidBy", gasto_actual.get("paidBy")))

        # 4. EL RE-CÁLCULO (Solo se ejecuta si es necesario)
        if recalcular_splits:
            # Traemos al grupo para ver a los integrantes
            grupo = db.groups.find_one({"_id": gasto_actual["groupId"]})
            miembros = grupo.get("members", [])
            cantidad_miembros = len(miembros)
            
            if cantidad_miembros > 0:
                monto_por_persona = round(nuevo_total / cantidad_miembros, 2)
                splits_recalculados = []
                
                for miembro in miembros:
                    usuario_id_str = str(miembro.get("userId"))
                    es_pagador = (usuario_id_str == nuevo_pagador)
                    
                    split = {
                        "userId": miembro.get("userId"),
                        "userName": miembro.get("displayName"),
                        "amountOwed": 0 if es_pagador else monto_por_persona,
                        "amountPaid": nuevo_total if es_pagador else 0,
                        "status": "settled" if es_pagador else "pending",
                        "settledAt": None
                    }
                    splits_recalculados.append(split)
                
                # Inyectamos los nuevos splits matemáticos a los datos que vamos a guardar
                datos_actualizados["splits"] = splits_recalculados

        # 5. Actualizamos la fecha de modificación
        datos_actualizados["updatedAt"] = datetime.utcnow()

        # 6. Guardamos los cambios finales en MongoDB
        db.shared_expenses.update_one(
            {"_id": ObjectId(gasto_id)},
            {"$set": datos_actualizados}
        )
        
        return True
    
    @staticmethod
    def eliminar_gasto(gasto_id):
        # 1. Ejecutamos la eliminación en la colección shared_expenses
        resultado = db.shared_expenses.delete_one({"_id": ObjectId(gasto_id)})
        
        # 2. Verificamos si realmente se borró algo (por si envían un ID falso o ya borrado)
        if resultado.deleted_count == 0:
            raise ValueError("El gasto especificado no existe o ya fue eliminado.")
            
        return True