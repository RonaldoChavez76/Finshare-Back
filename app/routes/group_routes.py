from flask import Blueprint
from app.controllers.group_controller import GroupController 
from app.utils.jwt_helper import jwt_required

groups_bp = Blueprint("groups", __name__, url_prefix="/api/groups")

# Todos protegidos
groups_bp.post("/")(jwt_required(GroupController.create))
groups_bp.get("/")(jwt_required(GroupController.list_mine))
groups_bp.get("/<group_id>")(jwt_required(GroupController.get))

# Miembros
groups_bp.post("/<group_id>/members")(jwt_required(GroupController.add_member))
groups_bp.delete("/<group_id>/members/<user_id>")(jwt_required(GroupController.remove_member))

# Desglose (solo owner/admin)
groups_bp.get("/<group_id>/breakdown")(jwt_required(GroupController.member_breakdown))
