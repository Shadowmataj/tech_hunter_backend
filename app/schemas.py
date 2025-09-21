"""
Module to handle api schemas.
This function allows to structure the
requests and the responses in our endpoints.
"""
from marshmallow import Schema, fields, EXCLUDE, post_dump, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from .models.user import UserModel, RoleModel
from .models.product import ProductModel, ProductImage, Twister
from passlib.hash import pbkdf2_sha256
from app.extensions import db


class RoleSchema(SQLAlchemyAutoSchema):
    """Role Schema"""
    class Meta:
        model = RoleModel
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE  

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class UserSchema(SQLAlchemyAutoSchema):
    """User Schema"""
    class Meta:
        model = UserModel
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE  

    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=False)
    last_name = fields.Str(required=False)
    birth_date = fields.Date(required=False)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    role = fields.Nested(RoleSchema, dump_only=True, required=False)




class UserRegisterSchema(SQLAlchemyAutoSchema):
    """User Register Schema"""
    class Meta:
        model = UserModel
        load_instance = True
        sqla_session = db.session
        include_fk = True
        nknown = EXCLUDE 

    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    birth_date = fields.Date(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    role = fields.Nested(RoleSchema, dump_only=True, load_default=2)
    
    @post_load
    def hash_password(self, data, **kwargs):
        """Reemplaza password en texto plano con el hash antes de crear User"""
        if "password" in data:
            data["password"] = pbkdf2_sha256.hash(data.pop("password"))
        return data


class ProductImageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProductImage
        load_instance = True
        include_fk = True  
        sqla_session = db.session
        nknown = EXCLUDE  

    id = fields.Int(dump_only=True)
    url = fields.Str(required=True)
    product_id = fields.Int(dump_only=True)


class TwisterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Twister
        load_instance = True
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE 

    id = fields.Int(dump_only=True)
    type = fields.Str(required=True)
    name = fields.Str(required=True)
    asin = fields.Str(required=True)
    product_id = fields.Int(dump_only=True)

    @post_dump
    def add_product_info(self, data, **kwargs):
        product = ProductModel.query.filter_by(asin=data["asin"]).first()
        if product and product.price != 0:
            key = f"product_{product.asin}"
            data[key] = {
                "asin": product.asin,
                "title": product.title,
                "price": product.price,
                "image": product.images[0].url,
                "url": product.url
            }
            if data["type"] == 'color_name':
                data[key]["color"] = data["name"]
            del data["name"]
            del data["asin"]
            del data["product_id"]
            del data["id"]
        else:
            data = {}
        return data


class ProductInputSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProductModel
        load_instance = True
        include_relationships = True
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE

    asin = fields.Str(required=True)
    price = fields.Float()
    url = fields.Str(required=True)
    title = fields.Str(required=True)
    brand = fields.Str()
    model = fields.Str()
    color = fields.Str()
    saving_percentage = fields.Int()
    basis_price = fields.Float()
    custumers_opinion = fields.Str()
    ranking = fields.Int(load_default=10000000)

    images = fields.List(fields.Nested(ProductImageSchema))
    twister = fields.List(fields.Nested(TwisterSchema))


class ProductOutputSchema(ProductInputSchema):

    images_examples = [
        "string",
        "string",
        "string",
    ]
    twister_example = {
        "type_name": {
            "product_asin": {
                "asin": "string",
                        "color": "string",
                        "image": "string",
                        "price": 0,
                        "title": "string",
                        "url": "string"
            }
        }
    }

    images = fields.List(
        fields.Nested(ProductImageSchema),
        metadata={"example": images_examples})
    twister = fields.List(
        fields.Nested(TwisterSchema),
        metadata={"example": twister_example})

    @post_dump
    def simplify_output(self, data, **kwards):

        simplified = {}

        for key, value in data.items():
            if not data[key]:
                continue
            simplified[key] = value

        simplified["images"] = [image["url"] for image in simplified["images"]]

        temp_dict = {}
        if simplified.get("twister"):      
            for twister in simplified["twister"]:
                if not len(twister):
                    continue
                tw_type = twister["type"]
                del twister["type"]
                if not temp_dict.get(tw_type):
                    temp_dict[tw_type] = {}

                temp_dict[tw_type] = twister

            if len(temp_dict):
                simplified["twister"] = temp_dict
            else:
                simplified.pop("twister")

        return simplified


class PaginationProductsSchema(Schema):

    products = fields.List(fields.Nested(ProductOutputSchema), dump_only=True)
    page = fields.Int(load_default=1)
    per_page = fields.Int(load_default=10)
    min_price = fields.Float(load_only=True)
    max_price = fields.Float(load_only=True)
    sort_by = fields.Str(load_default='ranking', load_only=True)  
    sort_order = fields.Str(load_default='asc', load_only=True) 
    total = fields.Integer(dump_only=True)
    pages = fields.Integer(dump_only=True)
    has_next = fields.Bool(dump_only=True)
    has_prev = fields.Bool(dump_only=True)

