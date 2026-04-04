from datetime import datetime
from bson.objectid import ObjectId

class GrupoModel:
    @staticmethod
    def estructura_base(datos):
        """
        Estructura base para la colección 'groups' según el documento oficial.
        El archivo 'service' debe proveer los valores para llenar este diccionario.
        """
        return {
            # "_id": ObjectId(), # MongoDB lo genera automáticamente 
            "name": str(datos.get("name")), 
            "description": str(datos.get("description")), 
            "groupType": str(datos.get("groupType")), # roommates | travel | project | other
            "ownerId": ObjectId(datos.get("ownerId")), # ref: users
            "isActive": bool(datos.get("isActive", True)), 
            "createdAt": datetime.utcnow(), 
            "updatedAt": datetime.utcnow(),
            
            "members": [
                {
                    "userId": ObjectId(datos.get("ownerId")), # ref: users 
                    "displayName": str(datos.get("displayName")), 
                    "role": "admin", # admin | member 
                    "joinedAt": datetime.utcnow(), 
                    "isActive": True 
                }
            ],
            
            "analytics": { 
                "stabilityIndex": float(datos.get("stabilityIndex", 100)), # (0-100) 
                "conflictRiskLevel": "low", # low | medium | high 
                "contributionVariance": float(0), 
                "dominantPayerId": None, # ObjectId | null 
                "calculatedAt": datetime.utcnow() 
            }
        }