"""
Resource to handle products endpoints.
It works with:
flask_smorest to create blueprints, routes, 
arguments and responses (the last two based on schemas).
"""

import sys

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.schemas import ProductOutputSchema, ProductInputSchema, PaginationProductsSchema
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError

from flask_jwt_extended import jwt_required, get_jwt

from ..models.product import ProductModel, ProductImage, Twister

from app.extensions import db

blp = Blueprint("products", __name__,
                description="Operations on products.", url_prefix="/api")


@blp.route("/product/amazon")
class Product(MethodView):

    @jwt_required()
    @blp.arguments(ProductInputSchema)
    @blp.response(201, ProductOutputSchema)
    def post(self, product_data: ProductModel):
        """Endpoint to post one product."""
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
    @blp.arguments(ProductInputSchema)
    @blp.response(200, ProductOutputSchema)
    def put(self, product_data, asin):

        product = ProductModel.query.filter_by(asin=asin).first()

        if not product:
            abort(404, message="Product not found")

        product.price = product_data.price
        product.url = product_data.url
        product.title = product_data.title
        product.brand = product_data.brand
        product.model = product_data.model
        product.saving_percentage = product_data.saving_percentage
        product.basis_price = product_data.basis_price
        product.custumers_opinion = product_data.custumers_opinion
        product.ranking = product_data.ranking

        if product_data.images:
            for image in product_data.images:
                db_image = ProductImage.query.filter_by(url=image.url)
                if not db_image:
                    product.images.append(image)

        if product_data.twister:
            for twister in product_data.twister:
                db_twister = Twister.query.filter_by(
                    asin=twister.asin, name=twister.name)
                if not db_twister:
                    product.twister.append(twister)

        db.session.commit()
        return product_data

    @jwt_required()
    @blp.response(200)
    def delete(self, asin):
        """Endpoint to delete a product using the asin."""
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
        sort_by = products_query.get("sort_by")  # campo por el que ordenar
        sort_order = products_query.get("sort_order")  # 'asc' o 'desc'

        query = ProductModel.query.filter(ProductModel.price != 0)

        # Filters
        if min_price is not None:
            query = query.filter(ProductModel.price >= min_price)
        if max_price is not None:
            query = query.filter(ProductModel.price <= max_price)

        # Order
        if hasattr(ProductModel, sort_by):
            column = getattr(ProductModel, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=True)
        print(pagination)

        return {
            "products": pagination.items,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }

    # @jwt_required()
    @blp.arguments(ProductInputSchema(many=True))
    @blp.response(201)
    def post(self, products_data: ProductModel):
        """Endpoint to post a list of products"""

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

    # @jwt_required()
    @blp.arguments(ProductInputSchema(many=True))
    def put(self, products_data):
        """Endpoint to update the products on data base."""

        count_updated = 0
        count_created = 0

        for data in products_data:
            asin = data.asin

            product = ProductModel.query.filter_by(asin=asin).first()
            count_updated += 1

            if not product:
                count_updated -= 1
                product = ProductModel(asin=asin)
                db.session.add(product)
                count_created += 1

            product.price = data.price
            product.url = data.url
            product.title = data.title
            product.brand = data.brand
            product.model = data.model
            product.saving_percentage = data.saving_percentage
            product.basis_price = data.basis_price
            product.custumers_opinion = data.custumers_opinion
            product.ranking = data.ranking
            product.images.clear()
            product.images = data.images
            product.twister.clear()
            product.twister = data.twister

            db.session.commit()

        return {
            "message": f"{count_updated} products updated successfully.",
            "c_message": f"{count_created} products were created."
        }

    @jwt_required()
    @blp.response(200)
    def delete(self):
        """Endpoint to delete ALL products."""
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
