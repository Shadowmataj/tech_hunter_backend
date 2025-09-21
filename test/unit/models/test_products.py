"""Unit tests for the ProductModel and its serialization/deserialization."""

from app.models import ProductModel
from app.extensions import db
from test.base_test import BaseTest
from app.schemas import ProductInputSchema, ProductOutputSchema


class ProductTest(BaseTest):
    """Unit tests for the ProductModel and its serialization/deserialization."""

    def setUp(self):
        """Set up test variables and initialize the database."""
        super().setUp()
        self.schema_in = ProductInputSchema()
        self.schema_out = ProductOutputSchema()
        self.first_test_product = {
            "asin": "TESTASIN123",
            "price": 100,
            "url": "https://test.com",
            "images": [{"url": "https://test.com/image.jpg"}],
            "title": "Test Product",
            "twister": [{
                    "type": "color_name",
                    "asin": "TESTASIN1234",
                    "name": "Test Color"}],
            "brand": "TEST",
            "model": "Test Model",
            "color": "Test Color",
            "saving_percentage": 1,
            "basis_price": 1,
            "custumers_opinion": "5 de 5 estrellas",
            "ranking": 1
        }
        self.second_test_product = {
            "asin": "TESTASIN1234",
            "url": "https://test.com",
            "title": "Test Product",
            "images": [{"url": "https://test.com/image.jpg"}],
            "price": 1,
        }
        self.test_products_list = [
            self.first_test_product,
            self.second_test_product
        ]
        self.new_product = self.schema_in.load(self.first_test_product)
        db.session.add(self.new_product)
        db.session.commit()

    def test_create_product(self):
        """Test creating a product and its storage in the database."""

        product = ProductModel.query.first()

        self.assertIsNotNone(product)
        self.assertEqual(product, self.new_product)

    def test_get_product(self):
        """Test retrieving a product and its serialization."""

        expected = {
            'asin': 'TESTASIN123',
                    'price': 100.0,
                    'url': 'https://test.com', ''
                    'title': 'Test Product',
                    'brand': 'TEST',
                    'model': 'Test Model',
                    'saving_percentage': 1,
                    'basis_price': 1.0,
                    'custumers_opinion': '5 de 5 estrellas',
                    'ranking': 1,
                    'images': [
                        'https://test.com/image.jpg'],
                    'twister': {
                        'color_name': {
                            'product_TESTASIN1234': {
                                'asin': 'TESTASIN1234',
                                'title': 'Test Product',
                                'price': 1.0,
                                'image': 'https://test.com/image.jpg',
                                'url': 'https://test.com', 'color': 'Test Color'}}},
                    'id': 1
        }

        new_product = self.schema_in.load(self.second_test_product)
        db.session.add(new_product)
        db.session.commit()

        product = ProductModel.query.first()

        product_data = self.schema_out.dump(product)

        self.assertIsNotNone(product_data)
        self.assertDictEqual(product_data, expected)

    def test_put_product(self):
        """Test updating a product."""

        product = ProductModel.query.first()
        self.assertEqual(product.price, 100)

        update_data = {"price": 50}
        updated_product = self.schema_in.load(update_data, instance=product, partial=True)
        db.session.add(updated_product)
        db.session.commit()

        updated_product_db = ProductModel.query.first()
        self.assertEqual(updated_product_db.price, 50)

    def test_delete_product(self):
        """Test deleting a product from the database."""

        product = ProductModel.query.first()
        self.assertIsNotNone(product)

        db.session.delete(product)
        db.session.commit()

        deleted_product = ProductModel.query.first()
        self.assertIsNone(deleted_product)
