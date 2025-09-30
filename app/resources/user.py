"""
Resource to handle users endpoints.
It works with:
flask_smorest to create blueprints, routes,
arguments and responses (the last two based on schemas).
"""

import datetime

from ..blocklist import BLOCKLIST
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy import or_
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
)

from ..extensions import db
from ..models import UserModel
from ..schemas import UserSchema, UserRegisterSchema
from ..utils.auth import role_filter

blp = Blueprint("users", __name__,
                description="Operations on tags", url_prefix="/api")


@blp.route("/register")
class UserRegister(MethodView):
    """Class to handle post"""

    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        """Endpoint to register a user."""
        if UserModel.query.filter(
                UserModel.email == user_data.email
        ).first():
            abort(409, message="A user with that email already exists.")

        db.session.add(user_data)
        db.session.commit()

        return {"message": "The user has been registered."}, 201


@blp.route("/login")
class UserLogin(MethodView):
    """Class to handle usre login."""

    @blp.arguments(UserSchema)
    def post(self, user_data):
        """Endpoint to login a user."""
        user = UserModel.query.filter(
            UserModel.email == user_data.email
        ).first()
        if user and pbkdf2_sha256.verify(user_data.password, user.password):
            access_token = create_access_token(
                identity=str(user.id),
                fresh=True,
                expires_delta=datetime.timedelta(minutes=60),
                additional_claims={"role": user.role.name})
            refresh_token = create_refresh_token(identity=str(
                user.id), expires_delta=datetime.timedelta(weeks=1))
            return {"access_token": access_token, "refresh_token": refresh_token}
        abort(401, message="Invalid credentials.")


@blp.route("/refresh")
class RefreshToken(MethodView):
    """Class to handle token refresh."""

    @jwt_required(refresh=True)
    def post(self):
        """Endpoint to handle token refresh."""
        current_user = get_jwt_identity()
        new_token = create_access_token(
            identity=current_user,
            fresh=False,
            additional_claims={
                "role": get_jwt().get("role")
            })
        return {"access_token": new_token}


@blp.route("/logout")
class UserLogout(MethodView):
    """Class to handle the logout."""

    @jwt_required()
    def post(self):
        """Endpoint to handle the logout."""
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}


@blp.route("/user/<int:user_id>")
class User(MethodView):
    """Class to handle the get and delete user by id."""

    @blp.response(200, UserSchema)
    @role_filter(["admin"])
    def get(self, user_id):
        """Endpoint to get a specific user by the id."""
        user = db.session.get(UserModel, user_id)
        if not user:
            abort(404, message="User not found.")
        return user

    @jwt_required()
    @role_filter(["admin"])
    def delete(self, user_id):
        """Endpoint to delete a specific user by the id."""

        user = db.session.get(UserModel, user_id)
        if not user:
            abort(404, message="User not found.")
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200
