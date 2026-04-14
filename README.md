<div align="center">
  <img src="https://img.icons8.com/color/96/000000/python.png" alt="Python Logo"/>
  <img src="https://img.icons8.com/color/96/000000/flask.png" alt="Flask Logo"/>
  <img src="https://img.icons8.com/color/96/000000/mongodb.png" alt="MongoDB Logo"/>
  
  <h1>FinShare Analytics - Backend API </h1>
  
  <p>
    <strong>El núcleo de lógica, procesamiento y almacenamiento de FinShare Analytics</strong>
  </p>

  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
  [![Flask](https://img.shields.io/badge/Flask-API-black.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248.svg?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
</div>

<br/>

Este repositorio contiene la **Restful API (Backend)** para la plataforma **FinShare Analytics**. Se encarga de gestionar toda la lógica de negocio, incluyendo la autenticación segura, la administración de grupos, transacciones financieras, cálculos matemáticos de riesgo y algoritmos de simulación. Todos los datos persisten a través de una base de datos NoSQL.

---

##  Características Principales

*    **Autenticación Segura:** Control de acceso mediante **JSON Web Tokens (JWT)**.
*    **Rendimiento Optimo:** Arquitectura segmentada en Controladores, Servicios y Rutas.
*    **Procesamiento Analítico:** Cálculos predictivos de riesgo financiero.
*    **CORS Configurado:** Completamente preparado para conectar sin problemas con clientes web (React).

---

##  Arquitectura del Proyecto

El proyecto está diseñado bajo un patrón estructural limpio para mantener la mantenibilidad del código:

```text
📦 Finshare-Back
 ┣ 📂 app
 ┃ ┣ 📂 controllers    # Lógica central de la aplicación
 ┃ ┣ 📂 routes         # Definición de Endpoints y delegación a controladores
 ┃ ┣ 📂 services       # Consultas e interacción directa con MongoDB 
 ┃ ┗ 📂 utils          # Herramientas compartidas (ej. validadores de tokens JWT)
 ┣ 📜 .env             # Variables de entorno secretas
 ┣ 📜 requirements.txt # Lista de dependencias del ecosistema Python
 ┗ 📜 run.py           # Punto de arranque principal de la API
```

---

##  Configuración y Uso Local

Para desplegar y correr tu servidor de desarrollo en tu propia PC, sigue estos sencillos pasos:

### 1. Prerrequisitos
Asegúrate de contar con las siguientes herramientas instaladas:
*   [Python 3.8+](https://www.python.org/downloads/)
*   [MongoDB](https://www.mongodb.com/try/download/community) (Ya sea de forma local mediante MongoDB Compass, o en la nube por Atlas).

### 2. Entorno Virtual

Es fundamental usar un entorno virtual (`venv`) en Python para no mezclar las librerías con las globales del sistema:

```bash
# 1. Crear el entorno virtual 
python -m venv venv

# 2. Activar el entorno virtual (En Windows)
venv\Scripts\activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

### 3. Configuración del Ambiente (`.env`)

Crea un archivo llamado `.env` en la raíz del proyecto (junto a `run.py`). Agrega tus claves de conexión y seguridad:

```ini
# Enlace de conexión a la Base de Datos
MONGO_URI=mongodb://localhost:27017/ 

# Llave de cifrado de seguridad JWT
JWT_SECRET=escribe_aqui_una_cadena_secreta_muy_segura
```

### 4. Ejecución del Servidor

Enciende el servidor en modo desarrollador ejecutando el siguiente comando:

```bash
python run.py
```
> 🎉 **¡Éxito!** El servidor iniciará correctamente y permanecerá a la escucha. Las peticiones del Frontend deberán apuntar hacia `http://localhost:5000`

---

## 📌 Inventario de Módulos (API)

| Método | Módulo | Ruta Base | Descripción de la Funcionalidad |
| :---: | :--- | :--- | :--- |
| `POST/GET` |  **Auth** | `/api/auth/` | Gestión integral de inicio de sesión, registros y perfil de usuario. |
| `GET` |  **Dashboard** | `/api/dashboard/` | Obtención de métricas consolidadas para las tarjetas principales. |
| `CRUD` |  **Grupos** | `/api/groups/` | Administración de finanzas compartidas y miembros. |
| `CRUD` |  **Transacciones**| `/api/transactions/`| Historial de movimientos y gastos individuales. |
| `GET` |  **Riesgos** | `/api/risk/` | Modelos de evaluación de impacto financiero. |
| `GET` |  **Simulador** | `/api/simulations/` | Proyecciones sobre diferentes alteraciones del gasto. |

<br/>
<div align="center">
  <i>Desarrollado para FinShare Analytics - Chávez Piñón Santiago Ronaldo - González Ávalos César Fernando - Torres Pérez Leonel Alejandro.</i>
</div>
