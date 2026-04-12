from flask import jsonify
from bson import ObjectId
from datetime import datetime
import json


class MongoJSONEncoder(json.JSONEncoder):
    """Serializa ObjectId y datetime para respuestas JSON."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize(obj):
    """Convierte ObjectIds y fechas en cualquier objeto (dict, list, etc.) a tipos JSON-safe."""
    if obj is None:
        return None
    return json.loads(json.dumps(obj, cls=MongoJSONEncoder))


def success_response(data=None, message: str = "OK", status: int = 200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = serialize(data)
    return jsonify(body), status


def error_response(message: str, status: int = 400, errors=None):
    body = {"success": False, "error": message}
    if errors:
        body["details"] = errors
    return jsonify(body), status


def paginated_response(items: list, total: int, page: int, per_page: int):
    return jsonify({
        "success": True,
        "data": [serialize(i) for i in items],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        },
    }), 200
