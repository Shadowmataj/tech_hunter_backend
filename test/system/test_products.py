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
            "image": "https://test.com/image.jpg",
            "alt": "Test Product",
            "title": "Test Product",
            "twister": [{
                    "type": "color_name",
                    "asin": "TESTASIN1234",
                    "name": "Test Color"}],
            "brand": "TEST",
            "model": "Test Model",
            "color": "Test Color",
            "basis_price": 1,
            "customers_opinion": 5,
            "ranking": 1
        }
        self.second_test_product = {
            "asin": "TESTASIN1234",
            "url": "https://test_second_updated.com",
            "title": "Test Second Product Update",
            "image": "https://test_second.com/image.jpg",
            "alt": "Test Second Product Update",
            "price": 10,
            "brand": "TEST_2"
        }
        roles = [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "user"}
        ]

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
        """Test for product creation endpoint."""
        expected = {
            "asin": "TESTASIN123",
            "price": 100.0,
            "url": "https://test.com",
            "title": "Test Product",
            "brand": "TEST",
            "model": "Test Model",
            "basis_price": 1.0,
            "customers_opinion": 5.0,
            "ranking": 1,
            "image": "https://test.com/image.jpg",
            "alt": "Test Product",
            "id": 1
        }

        response = self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(response.json, expected)

    def test_post_products(self):
        """Test for products creation endpoint."""
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
        """Test for posting a duplicated product."""
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
        """Test for getting a product by its ASIN."""
        expected = {
            'alt': 'Test Product',
            'asin': 'TESTASIN123',
            'basis_price': 1.0,
            'brand': 'TEST',
            'customers_opinion': 5.0,
            'id': 1,
            'image': 'https://test.com/image.jpg',
            'model': 'Test Model',
            'price': 100.0,
            'ranking': 1,
            'title': 'Test Product',
            'url': 'https://test.com'
        }
        self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            f"/api/product/amazon/{self.first_test_product["asin"]}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected)

    def test_get_products(self):
        """Test for getting all products."""
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
        self.assertListEqual(response.json["brands"], ["TEST_2", "TEST"])

    def test_get_products_query(self):
        """Test for getting products with query parameters."""
        products = [self.first_test_product,
                    self.second_test_product, self.second_test_product]
        query = {
            "page": 2,
            "per_page": 1,
            "min_price": 0,
            "max_price": 100,
            "sort_by": "price",
            "sort order": "desc",
            "brands": [
                self.first_test_product["brand"],
                self.second_test_product["brand"]
            ]
        }

        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            f"/api/products/amazon",
            query_string=query
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["products"]), 1)
        self.assertEqual(response.json["has_next"], False)
        self.assertEqual(response.json["has_prev"], True)
        self.assertEqual(response.json["page"], 2)
        self.assertEqual(response.json["pages"], 2)
        self.assertEqual(response.json["per_page"], 1)
        self.assertEqual(response.json["total"], 2)
        self.assertListEqual(response.json["brands"], ["TEST_2", "TEST"])

    def test_put_product(self):
        """Test for updating a product."""
        products = [self.first_test_product,
                    self.second_test_product, self.second_test_product]

        updated_product = {
            "asin": "TESTASIN123",
            "price": 1000,
            "url": "https://test_updated.com.mx",
            "image": "https://test_updated.com/image.jpg",
            "alt": "Test Product Updated",
            "title": "Test Product Updated",
            "twister": [
                {
                    "type": "color_name",
                    "asin": "TESTASIN1234",
                    "name": "Second test Color"
                },
                {
                    "type": "style_name",
                    "asin": "TESTASIN1234",
                    "name": "Test Style"
                }

            ],
            "brand": "TEST_UPDATED",
            "model": "Test Model Update",
            "color": "Test Color Update",
            "customers_opinion": 0,
            "ranking": 2
        }

        expected = {
            'alt': 'Test Product Updated',
            'asin': 'TESTASIN123',
            'brand': 'TEST_UPDATED',
            'id': 1,
            'image': 'https://test_updated.com/image.jpg',
            'model': 'Test Model Update',
            'price': 1000.0,
            'ranking': 2,
            'title': 'Test Product Updated',
            'twister': {
                'color_name': {
                    'product_TESTASIN1234': {
                        'alt': 'Test Second Product Update',
                        'asin': 'TESTASIN1234',
                        'color': 'Second test Color',
                        'image': 'https://test_second.com/image.jpg',
                        'price': 10.0,
                        'title': 'Test Second Product Update',
                        'url': 'https://test_second_updated.com'
                    }
                },
                'style_name': {
                    'product_TESTASIN1234': {
                        'alt': 'Test Second Product Update',
                        'asin': 'TESTASIN1234',
                        'image': 'https://test_second.com/image.jpg',
                        'price': 10.0,
                        'title': 'Test Second Product Update',
                        'url': 'https://test_second_updated.com'
                    }
                }
            },
            'url': 'https://test_updated.com.mx'
        }
        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        put_response = self.client.put(
            f"/api/product/amazon/{self.first_test_product["asin"]}",
            json=updated_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(put_response.status_code, 200)

        response = self.client.get(
            f"/api/product/amazon/{self.first_test_product["asin"]}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json, expected)

    def test_put_products(self):
        """Test for updating multiple products."""
        products = [self.first_test_product,
                    self.second_test_product]

        updated_products = [{
            "alt": "Test Product Updated",
            "asin": "TESTASIN123",
            "price": 1000,
            "url": "https://test_updated.com.mx",
            "image": "https://test_updated.com/image.jpg",
            "title": "Test Product Updated",
            "twister": [
                {
                    "type": "color_name",
                    "asin": "TESTASIN1234",
                    "name": "Second test Color"
                },
                {
                    "type": "style_name",
                    "asin": "TESTASIN1234",
                    "name": "Test Style"
                }
            ],
            "brand": "TEST_UPDATED",
            "model": "Test Model Update",
            "color": "Test Color Update",
            "customers_opinion": 0,
            "ranking": 2
        },
            {
            "alt": "Test Second Product Update",
            "asin": "TESTASIN1234",
            "url": "https://test_second_updated.com",
            "title": "Test Second Product Update",
            "image": "https://test_second.com/image.jpg",
            "price": 10,
        },
            {
            "alt": "Test Third Product",
            "asin": "TESTASIN12345",
            "url": "https://test_third.com",
            "title": "Test Third Product",
            "image": "https://test_third.com/image.jpg",
            "price": 1,
        }
        ]

        expected = {
            'alt': 'Test Product Updated',
            'asin': 'TESTASIN123',
            'brand': 'TEST_UPDATED',
            'id': 1,
            'image': 'https://test_updated.com/image.jpg',
            'model': 'Test Model Update',
            'price': 1000.0,
            'ranking': 2,
            'title': 'Test Product Updated',
            'twister': {
                'color_name': {
                    'product_TESTASIN1234': {
                        'alt': 'Test Second Product Update',
                        'asin': 'TESTASIN1234',
                        'color': 'Second test Color',
                        'image': 'https://test_second.com/image.jpg',
                        'price': 10.0,
                        'title': 'Test Second Product Update',
                        'url': 'https://test_second_updated.com'
                    }
                },
                'style_name': {
                    'product_TESTASIN1234': {
                        'alt': 'Test Second Product Update',
                        'asin': 'TESTASIN1234',
                                'image': 'https://test_second.com/image.jpg',
                                'price': 10.0,
                                'title': 'Test Second Product Update',
                                'url': 'https://test_second_updated.com'
                    }
                }
            },
            'url': 'https://test_updated.com.mx'
        }
        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.put(
            f"/api/products/amazon",
            json=updated_products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["message"],
            "2 products updated successfully.")
        self.assertEqual(
            len(response.json["to_create"]),
            1)

        response = self.client.get(
            f"/api/product/amazon/{self.first_test_product["asin"]}")

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected, response.json)

    def test_delete_product(self):
        """Test for deleting a product."""
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
        """Test for deleting all products."""
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
        self.assertEqual(
            response.json["message"],
            "2 products have been deleted.")

    def test_get_products_ids(self):
        """Test for getting all product IDs."""
        products = [self.first_test_product, self.second_test_product]
        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            "/api/products/amazon/id",
            headers={
                "Authorization": f"Bearer {self.access_token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.json["asins"],
            [product["asin"] for product in products])

    def test_get_brands(self):
        """Test for getting all product brands."""
        products = [self.first_test_product, self.second_test_product]
        self.client.post(
            "/api/products/amazon",
            json=products,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        response = self.client.get(
            "/api/brands/amazon",
            headers={
                "Authorization": f"Bearer {self.access_token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.json["brands"],
            [product["brand"] for product in products[::-1]])

    def test_patch_products_update(self):
        """Test for partially updating a product."""
        self.client.post(
            "/api/product/amazon",
            json=self.first_test_product,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        patch_data = [{
            'asin': 'TESTASIN123',
            'price': 15067.0,
            'url': 'https://www.test.com.mx/nubia-5g-Android-unlocke-Cellphone/dp/B0F66GWJ9C',
            'image': 'https://m.media-test.com/image/I/71rgOENcn7L._AC_UL320_.jpg',
            'alt': 'test unlocke Cellphone',
            'title': 'test unlocke cellphone',
            'customers_opinion': 4.6,
            'basis_price': 15999.0
        }]

        expected = {
            'alt': 'test unlocke Cellphone',
            'asin': 'TESTASIN123',
            'basis_price': 15999.0,
            'brand': 'TEST',
            'customers_opinion': 4.6,
            'id': 1,
            'image': 'https://m.media-test.com/image/I/71rgOENcn7L._AC_UL320_.jpg',
            'model': 'Test Model',
            'price': 15067.0,
            'ranking': 1,
            'title': 'test unlocke cellphone',
            'url': 'https://www.test.com.mx/nubia-5g-Android-unlocke-Cellphone/dp/B0F66GWJ9C'
            }

        patch_response = self.client.patch(
            f"/api/products/amazon",
            json=patch_data,
            headers={
                "Authorization": f"Bearer {self.access_token}"})

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(
            patch_response.json["message"],
            "1 products updated successfully.")

        response = self.client.get(
            f"/api/product/amazon/{self.first_test_product["asin"]}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json, expected)
