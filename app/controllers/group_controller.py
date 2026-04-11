from flask import request, jsonify
from marshmallow import ValidationError
from app.services.group_service import GroupService
from app.schemas.group_schemas import CreateGroupSchema, AddMemberSchema
from app.utils.responses import success_response, error_response

# Instanciamos los schemas para validación
_create_schema     = CreateGroupSchema()
_add_member_schema = AddMemberSchema()

class GroupController:

    @staticmethod
    def create():
        try:
            data = _create_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            # Nota: Usamos request.current_user_id (asumiendo que viene de un decorador JWT)
            group = GroupService.create_group(
                owner_id=getattr(request, 'current_user_id', None) or data.get("ownerId"),
                name=data["name"],
                description=data.get("description", ""),
                group_type=data.get("groupType", "other"),
            )
        except ValueError as e:
            return error_response(str(e), 400)
        return success_response(group, "Grupo creado", 201)

    @staticmethod
    def list_mine():
        user_id = getattr(request, 'current_user_id', None)
        if not user_id:
            return error_response("Usuario no identificado", 401)
        groups = GroupService.get_user_groups(user_id)
        return success_response(groups)

    @staticmethod
    def list_all():
        """Adaptación del 'obtener_todos_los_grupos' del compañero"""
        try:
            groups = GroupService.get_all_groups()
            return success_response(groups, "Grupos obtenidos exitosamente")
        except Exception as e:
            return error_response("Error al obtener grupos", 500, str(e))

    @staticmethod
    def update(group_id: str):
        """Adaptación del 'editar_grupo' del compañero"""
        try:
            data = request.get_json()
            changed = GroupService.update_group(group_id, data)
            message = "Grupo actualizado" if changed else "No hubo cambios"
            return success_response({"groupId": group_id}, message)
        except ValueError as e:
            return error_response(str(e), 404)
        except Exception as e:
            return error_response("Error interno al actualizar", 500, str(e))

    @staticmethod
    def delete(group_id: str):
        """Adaptación del 'eliminar_grupo' del compañero"""
        try:
            GroupService.delete_group(group_id)
            return success_response({"groupId": group_id}, "Grupo eliminado correctamente")
        except ValueError as e:
            return error_response(str(e), 404)
        except Exception as e:
            return error_response("Error interno al eliminar", 500, str(e))

    @staticmethod
    def add_member(group_id: str):
        # 1. Obtenemos los datos crudos
        json_data = request.get_json() or {}
        email = json_data.get("email")

        # 2. Si viene un email, ignoramos el esquema estricto y vamos directo al Service
        if email:
            try:
                # Usamos la función inteligente que ya tienes en el Service
                nuevo_miembro = GroupService.add_member(group_id, email)
                return success_response(nuevo_miembro, "Miembro agregado por email", 201)
            except ValueError as e:
                return error_response(str(e), 400)
            except Exception as e:
                return error_response("Error al procesar la invitación", 500, str(e))

        # 3. Si NO viene email, seguimos con la lógica original de tus compañeros (por si acaso)
        try:
            data = _add_member_schema.load(json_data)
            group = GroupService.add_member_by_id( # Tendrías que tener este método o ajustar
                group_id=group_id,
                requester_id=request.current_user_id,
                user_id=data["userId"],
                display_name=data.get("displayName", ""),
                role=data.get("role", "member"),
            )
            return success_response(group, "Miembro agregado")
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        except Exception as e:
            return error_response(str(e), 400)

    @staticmethod
    def remove_member(group_id: str, user_id: str):
        try:
            group = GroupService.remove_member(group_id, request.current_user_id, user_id)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 400
            return error_response(str(e), status)
        return success_response(group, "Miembro removido")

    @staticmethod
    def member_breakdown(group_id: str):
        try:
            data = GroupService.get_member_breakdown(group_id, request.current_user_id)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 400
            return error_response(str(e), status)
        return success_response(data)


    @staticmethod
    def get(group_id: str):
        """Obtiene un grupo específico por su ID"""
        try:
            # Asegúrate de que tu Service tenga el método get_group
            group = GroupService.get_group(group_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        except PermissionError as e:
            return error_response(str(e), 403)
        return success_response(group)

# --- PUENTES DE COMPATIBILIDAD (Para que el código del compañero no explote) ---
GroupController.crear_grupo = GroupController.create
GroupController.editar_grupo = GroupController.update
GroupController.eliminar_grupo = GroupController.delete
GroupController.obtener_todos_los_grupos = GroupController.list_all