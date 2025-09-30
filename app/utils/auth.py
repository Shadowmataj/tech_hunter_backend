"""Authentication Utilities
This module provides utility functions for handling authentication and authorization
using Flask-JWT-Extended. It includes decorators to enforce role-based access control.
"""

from flask_jwt_extended import (
    jwt_required,
    get_jwt,
)
from flask_smorest import abort
from functools import wraps


def role_filter(roles: list) -> callable:

    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                abort(403, message="Admin privilege required.")
            return fn(*args, **kwargs)
        return decorated
    return wrapper
