"""Product model."""
from ..extensions import db

class ProductModel(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(20), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.Text, nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    basis_price = db.Column(db.Float, nullable=True)
    customers_opinion = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    alt = db.Column(db.String(255), nullable=True)

    # Relationship to Twister model
    twister = db.relationship("Twister", backref="product", lazy=True, cascade="all, delete-orphan")


class Twister(db.Model):
    """Twister model for product variations."""
    __tablename__ = "twister"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)   # "style_name", "color_name", "size_name"
    name = db.Column(db.String(100), nullable=False)  # e.g. "Cosmic Black"
    asin = db.Column(db.String(20), nullable=False)   # e.g. "B082XY6YYZ"
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

