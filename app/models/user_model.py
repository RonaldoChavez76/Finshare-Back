from datetime import datetime, timezone
from bson import ObjectId
import bcrypt

# 1. Proyección para limpiar datos sensibles en consultas
PUBLIC_PROJECTION = {
    "passwordHash": 0,
    "createdAt": 0,
    "updatedAt": 0
}

# 2. Constructor de Usuario (con 4 argumentos: fullName, email, password, phone)
def build_user(full_name, email, password, phone=None):
    now = datetime.now(timezone.utc)
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    return {
        "_id": ObjectId(),
        "fullName": full_name,
        "email": email.lower().strip(),
        "passwordHash": hashed_password.decode('utf-8'),
        "phone": phone,
        "finance": {
            "totalBalance": 0.0,
            "monthlyIncome": 0.0,
            "monthlyExpenses": 0.0,
            "currency": "MXN"
        },
        "isActive": True,
        "createdAt": now,
        "updatedAt": now
    }

# 3. Verificador de contraseñas para el Login
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

# 4. Constructor de Deudas (La pieza que faltaba)
def build_debt(description, amount, status="pending"):
    """Estructura el objeto de una deuda dentro del perfil de usuario"""
    return {
        "debtId": ObjectId(),
        "description": description,
        "amount": float(amount),
        "status": status, # pending | paid
        "createdAt": datetime.now(timezone.utc)
    }