from flask import Blueprint, request, jsonify
from app.services.grupo_service import GrupoService

# Creamos el Blueprint para las rutas de grupos
grupo_bp = Blueprint('grupo_bp', __name__)

# Definimos la ruta POST para crear el grupo
@grupo_bp.route('/crear', methods=['POST'])
def crear_grupo():
    # Extraemos el JSON que nos enviará React
    datos = request.json
    
    try:
        # Le pasamos el paquete de datos al Servicio para que haga el trabajo
        nuevo_grupo_id = GrupoService.crear_grupo(datos)
        
        # Si todo sale bien, respondemos con un código 201 (Created)
        return jsonify({
            "mensaje": "Grupo creado exitosamente",
            "grupo_id": nuevo_grupo_id
        }), 201
        
    except ValueError as error_validacion:
        # Si faltaron datos (nombre u ownerId), respondemos con error 400 (Bad Request)
        return jsonify({"error": str(error_validacion)}), 400
        
    except Exception as e:
        # Si MongoDB explota o hay un error de código, respondemos con 500
        return jsonify({
            "error": "Error interno del servidor",
            "detalle": str(e)
        }), 500

@grupo_bp.route('/<grupo_id>', methods=['PATCH'])
def editar_grupo(grupo_id):
    datos = request.json
    
    try:
        # Pasamos el ID y los datos al servicio
        hubo_cambios = GrupoService.actualizar_grupo(grupo_id, datos)
        
        if hubo_cambios:
            return jsonify({
                "mensaje": "Grupo actualizado correctamente",
                "grupo_id": grupo_id
            }), 200
        else:
            return jsonify({
                "mensaje": "El grupo existe, pero los datos enviados son iguales a los actuales (no hubo cambios)."
            }), 200
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404 # 404 Not Found o 400 Bad Request
    except Exception as e:
        return jsonify({"error": "Error interno al actualizar el grupo", "detalle": str(e)}), 500
    
@grupo_bp.route('/', methods=['GET'])
def obtener_todos_los_grupos():
    try:
        # Llamamos al servicio para que traiga y limpie la lista
        lista_grupos = GrupoService.obtener_todos_los_grupos()
        
        return jsonify({
            "mensaje": "Grupos obtenidos exitosamente",
            "total_grupos": len(lista_grupos),
            "grupos": lista_grupos
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Error interno al obtener los grupos", "detalle": str(e)}), 500
    
@grupo_bp.route('/<grupo_id>', methods=['DELETE'])
def eliminar_grupo(grupo_id):
    try:
        # Llamamos al servicio para ejecutar la eliminación
        GrupoService.eliminar_grupo(grupo_id)
        
        return jsonify({
            "mensaje": "Grupo eliminado correctamente",
            "grupo_id": grupo_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404 # 404 Not Found si no existe
    except Exception as e:
        return jsonify({"error": "Error interno al eliminar el grupo", "detalle": str(e)}), 500