"""Users model."""
from db import db

class UserModel(db.Model):
    """Users model."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email= db.Column(db.String, nullable=True, unique=True)
    password = db.Column(db.String(100), nullable=False)

