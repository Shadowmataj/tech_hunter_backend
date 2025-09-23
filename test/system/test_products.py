from test.base_test import BaseTest
from app.extensions import db
from app.models.user import RoleModel
from app.schemas import UserRegisterSchema


class TestProducts(BaseTest):
    """Test case for products."""

    def setUp(self):
        """Set up test variables and initialize the database."""
        super().setUp()
        self.admin_user = {
            "first_name": "Admin_name",
            "last_name": "Admin_lastname",
            "birth_date": "1985-05-05",
            "email": "test_admin@mail.com",
            "password": "admin123",
            "role_id": 1
        }
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
        roles = [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "user"}
        ]
        self.expected = {
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
                    'id': 1
        }

        for role_data in roles:
            role = RoleModel(**role_data)
            db.session.add(role)
        db.session.commit()

        new_user = UserRegisterSchema().load(self.admin_user)
        db.session.add(new_user)
        db.session.commit()

        login_response = self.client.post("/api/login", json={
            "email": self.admin_user["email"],
            "password": self.admin_user["password"]
        })
        self.access_token = login_response.json["access_token"]

    def test_post_product(self):
        """"""

        response = self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(response.json, self.expected)

    def test_post_products(self):
        """"""
        products = [self.first_test_product,
                    self.second_test_product, self.second_test_product]

        response = self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json["message"],
            "The products have been created.")
        self.assertEqual(response.json["repeated_products"], 1)

    def test_post_duplicated_product(self):
        """"""
        for _ in range(2):
            response = self.client.post(
                "/api/product/amazon",
                json=self.first_test_product,
                headers={
                    "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json["message"],
            "A product with that ASIN already exists.")
        self.assertEqual(response.json["status"], "Conflict")

    def test_get_product(self):
        """"""

        self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            f"/api/product/amazon/{self.first_test_product["asin"]}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, self.expected)

    def test_get_products(self):
        """"""
        products = [self.first_test_product,
                    self.second_test_product, self.second_test_product]

        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            f"/api/products/amazon"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["products"]), 2)
        self.assertEqual(response.json["has_next"], False)
        self.assertEqual(response.json["has_prev"], False)
        self.assertEqual(response.json["page"], 1)
        self.assertEqual(response.json["pages"], 1)
        self.assertEqual(response.json["per_page"], 10)
        self.assertEqual(response.json["total"], 2)

    def test_delete_product(self):
        """"""
        self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.delete(
            f"/api/product/amazon/{self.first_test_product["asin"]}",
            headers={
                "Authorization": f"Bearer {self.access_token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["message"],
            "The product has been deleted.")

    def test_delete_all_products(self):
        """"""
        products = [self.first_test_product, self.second_test_product]

        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.delete(
            "/api/products/amazon",
            headers={
                "Authorization": f"Bearer {self.access_token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "2 products have been deleted.")
