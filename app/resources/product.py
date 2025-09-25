"""
Resource to handle products endpoints.
It works with:
flask_smorest to create blueprints, routes, 
arguments and responses (the last two based on schemas).
"""

import sys

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from ..schemas import (
    ProductOutputSchema, 
    ProductInputSchema, 
    PaginationProductsSchema, 
    ProductPutSchema,
    ProductsColumns)
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError

from flask_jwt_extended import jwt_required, get_jwt

from ..models.product import ProductModel, ProductImage, Twister

from ..extensions import db

blp = Blueprint("products", __name__,
                description="Operations on products.", url_prefix="/api")


@blp.route("/product/amazon")
class Product(MethodView):

    @jwt_required()
    @blp.arguments(ProductInputSchema)
    @blp.response(201, ProductOutputSchema)
    def post(self, product_data: ProductModel):
        """Endpoint to post one product."""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        if ProductModel.query.filter_by(asin=product_data.asin).first():
            abort(409, message="A product with that ASIN already exists.")
        try:
            db.session.add(product_data)
            db.session.commit()
        except Exception as e:
            print(f"Error adding product: {e}", file=sys.stderr)
            abort(500, message="An error occurred while inserting the product.")

        return product_data


@blp.route("/product/amazon/<string:asin>")
class ProductOperations(MethodView):
    """Class to get specific products"""

    @blp.response(200, ProductOutputSchema)
    def get(self, asin):
        """Endpoint to get a product by its asin, with optional filters."""
        product = ProductModel.query.filter_by(asin=asin).first_or_404()

        return product

    @jwt_required()
    @blp.arguments(ProductPutSchema)
    @blp.response(200, ProductOutputSchema)
    def put(self, product_data, asin):
        """"""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        with db.session.no_autoflush:
            product = ProductModel.query.filter_by(
                asin=asin).first()

            if not product:
                abort(404, message="Product not found")

            for column in ProductModel.__table__.columns.keys():
                if column == "id":
                    continue
                if column in product_data:
                    setattr(product, column, product_data[column])
                else:
                    setattr(product, column, None)

            if product_data.get("images"):
                product.images.clear()
                for image in product_data["images"]:
                    product.images.append(ProductImage(**image))

            product.twister.clear()
            if product_data.get("twister"):
                for twister in product_data["twister"]:
                    product.twister.append(Twister(**twister))
                    db.session.commit()
        return product_data

    @jwt_required()
    @blp.response(200)
    def delete(self, asin):
        """Endpoint to delete a product using the asin."""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        product = ProductModel.query.filter_by(asin=asin).first_or_404()

        db.session.delete(product)
        db.session.commit()

        return {"message": "The product has been deleted."}


@blp.route("/products/amazon")
class ProductsList(MethodView):
    """Class to get all the Products"""

    @blp.arguments(PaginationProductsSchema, location='query')
    @blp.response(200, PaginationProductsSchema)
    def get(self, products_query):
        """Endpoint to get all products, with optional filters."""

        page = products_query.get("page")
        per_page = products_query.get("per_page")
        min_price = products_query.get("min_price")
        max_price = products_query.get("max_price")
        sort_by = products_query.get("sort_by")
        sort_order = products_query.get("sort_order")
        brands = products_query.get("brands")

        query = ProductModel.query.filter(ProductModel.price != 0)

        # Filters
        if min_price is not None:
            query = query.filter(ProductModel.price >= min_price)
        if max_price is not None:
            query = query.filter(ProductModel.price <= max_price)

        # Brand
        if len(brands):
            query = query.filter(ProductModel.brand.in_(brands))

        # Order
        if hasattr(ProductModel, sort_by):
            column = getattr(ProductModel, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=True)

        brands = db.session.execute(
            db.select(ProductModel.brand).distinct()).scalars().all()

        return {
            "products": pagination.items,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "brands": brands
        }

    @jwt_required()
    @blp.arguments(ProductInputSchema(many=True))
    @blp.response(201)
    def post(self, products_data: ProductModel):
        """Endpoint to post a list of products"""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        new_products = []
        repeated_count = 0

        for product_data in products_data:

            if ProductModel.query.filter_by(asin=product_data.asin).first():
                repeated_count += 1
                continue

            db.session.add(product_data)
            new_products.append(product_data)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error adding product: {e}", file=sys.stderr)
            abort(500, message="An error occurred while inserting the product.")

        return {"message": "The products have been created.", "repeated_products": repeated_count}

    @jwt_required()
    @blp.arguments(ProductPutSchema(many=True))
    def put(self, products_data):
        """Endpoint to update the products on data base."""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        count_updated = 0
        to_create = []

        for data in products_data:
            with db.session.no_autoflush:
                product = ProductModel.query.filter_by(
                    asin=data["asin"]).first()

            if product:
                count_updated += 1
                for column in ProductModel.__table__.columns.keys():
                    if column == "id":
                        continue
                    if column in data:
                        setattr(product, column, data[column])
                    else:
                        setattr(product, column, None)

                if data.get("images"):
                    product.images.clear()
                    for image in data["images"]:
                        product.images.append(ProductImage(**image))

                product.twister.clear()
                if data.get("twister"):
                    for twister in data["twister"]:
                        product.twister.append(Twister(**twister))
                        db.session.commit()
            else:
                to_create.append(data["asin"])

        db.session.commit()
        return {
            "message": f"{count_updated} products updated successfully.",
            "to_create": to_create
        }

    @jwt_required()
    @blp.response(200)
    def delete(self):
        """Endpoint to delete ALL products."""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        try:
            # Delete all records in ProductModel
            products = ProductModel.query.all()
            count = 0

            for product in products:
                db.session.delete(product)
                count += 1

            db.session.commit()

            return {"message": f"{count} products have been deleted."}

        except SQLAlchemyError as e:
            print(f"Error deleting products: {e}", file=sys.stderr)
            db.session.rollback()
            abort(500, {"error": str(e)})


@blp.route("/products/amazon/id")
class ProductsIdList(MethodView):
    """Class to get all the Products IDs"""

    @jwt_required()
    @blp.response(200, ProductsColumns)
    def get(self):
        """Endpoint to get all the IDs"""
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        asins_list = db.session.execute(
            db.select(ProductModel.asin)).scalars().all()
        
        return {"asins": asins_list}
    
@blp.route("/brands/amazon")
class ProductBrandsList(MethodView):
    """Class to get all the Products brands"""

    @jwt_required()
    @blp.response(200, ProductsColumns)
    def get(self):
        """Endpoint to get all the brands on database."""

        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        brands_list = db.session.execute(
            db.select(ProductModel.brand).distinct()
        ).scalars().all()

        return {"brands": brands_list}