from flask import Blueprint, request, jsonify
from app.services.gasto_service import GastoService

gasto_bp = Blueprint('gasto_bp', __name__)

@gasto_bp.route('/crear', methods=['POST'])
def crear_gasto():
    datos = request.json
    
    # Validaciones rápidas
    if not datos.get("groupId") or not datos.get("totalAmount") or not datos.get("paidBy"):
        return jsonify({"error": "Faltan datos obligatorios (groupId, totalAmount, paidBy)"}), 400
        
    try:
        # Pasamos el trabajo pesado al servicio
        nuevo_gasto_id = GastoService.crear_gasto_con_division(datos)
        
        return jsonify({
            "mensaje": "Gasto registrado y dividido correctamente",
            "gasto_id": nuevo_gasto_id
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Error interno", "detalle": str(e)}), 500
    
    
    
@gasto_bp.route('/grupo/<grupo_id>/saldos', methods=['GET'])
def obtener_saldos(grupo_id):
    try:
        # Llamamos al servicio para que haga toda la suma
        saldos_calculados = GastoService.obtener_saldos_grupo(grupo_id)
        
        return jsonify({
            "mensaje": "Saldos calculados exitosamente",
            "grupo_id": grupo_id,
            "saldos": saldos_calculados
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Error interno al calcular saldos", "detalle": str(e)}), 500
    

@gasto_bp.route('/<gasto_id>', methods=['PATCH'])
def editar_gasto(gasto_id):
    datos = request.json
    
    try:
        # Enviamos los datos al servicio inteligente
        GastoService.actualizar_gasto(gasto_id, datos)
        
        return jsonify({
            "mensaje": "Gasto actualizado correctamente (se recalcularon los saldos si fue necesario)",
            "gasto_id": gasto_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Error interno al actualizar el gasto", "detalle": str(e)}), 500
    
@gasto_bp.route('/<gasto_id>', methods=['DELETE'])
def eliminar_gasto(gasto_id):
    try:
        # Llamamos al servicio para que destruya el registro
        GastoService.eliminar_gasto(gasto_id)
        
        return jsonify({
            "mensaje": "Gasto eliminado correctamente. Los saldos del grupo se han ajustado automáticamente.",
            "gasto_id": gasto_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404 # 404 Not Found
    except Exception as e:
        return jsonify({"error": "Error interno al eliminar el gasto", "detalle": str(e)}), 500