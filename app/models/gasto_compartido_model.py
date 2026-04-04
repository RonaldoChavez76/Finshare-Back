from datetime import datetime
from bson.objectid import ObjectId

class GastoCompartidoModel:
    @staticmethod
    def estructura_base(datos, splits_calculados):
        """
        Estructura base para la colección 'shared_expenses'.
        'splits_calculados' es el arreglo que tu algoritmo matemático generará.
        """
        return {
            # "_id": ObjectId(), # MongoDB lo genera automáticamente 
            "groupId": ObjectId(datos.get("groupId")), # ref: groups 
            "paidBy": ObjectId(datos.get("paidBy")), # ref: users 
            "paidByName": str(datos.get("paidByName")), 
            "concept": str(datos.get("concept")), 
            "totalAmount": float(datos.get("totalAmount")), 
            "currency": str(datos.get("currency", "MXN")), # MXN | USD 
            "category": str(datos.get("category")), # food | rent | transport | entertainment | services | other 
            "expenseDate": datos.get("expenseDate", datetime.utcnow()),
            "status": "pending", # pending | partial | settled 
            "createdAt": datetime.utcnow(), 
            "updatedAt": datetime.utcnow(), 
            
            # Este es el resultado del algoritmo de tu servicio 
            "splits": splits_calculados 
            # Estructura interna de cada objeto en 'splits':
            # {
            #     "userId": ObjectId(), # ref: users 
            #     "userName": "String",  
            #     "amountOwed": Number,  
            #     "amountPaid": Number, 
            #     "status": "pending | partial | settled",
            #     "settledAt": Date | null  
            # }
        }