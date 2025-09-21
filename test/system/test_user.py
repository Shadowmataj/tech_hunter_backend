from test.base_test import BaseTest
from app.extensions import db
from app.models.user import RoleModel, UserModel


class UserTest(BaseTest):
    """Unit tests for the UserModel and its serialization/deserialization."""
    
    def setUp(self):
        """Set up test variables and initialize the database."""
        super().setUp()
        self.test_user = {
            "first_name": "Test_name",
            "last_name": "Test_lastname",
            "birth_date": "1990-01-01",
            "email": "test@mail.com",
            "password": "123456",
        }

        self.admin_user = {
            "first_name": "Admin_name",
            "last_name": "Admin_lastname",
            "birth_date": "1985-05-05",
            "email": "test_admin@mail.com",
            "password": "admin123",
        }

        roles = [
            {"id": 1, "name": "user"},
            {"id": 2, "name": "admin"}
        ]
        for role_data in roles:
            role = RoleModel(**role_data)
            db.session.add(role)
        db.session.commit()

    def test_register_user(self):
        """Test user registration."""

        response = self.client.post("/api/register", json=self.test_user)
        self.assertEqual(response.status_code, 201)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "The user has been registered.")

    def test_register_existing_user(self):
        """Test registering a user that already exists."""

        self.client.post("/api/register", json=self.test_user)
        response = self.client.post("/api/register", json=self.test_user)
        self.assertEqual(response.status_code, 409)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "A user with that email already exists.")


    def test_login_user(self):
        """Test user login."""

        self.client.post("/api/register", json=self.test_user)

        response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json)
        self.assertIn("refresh_token", response.json)

    def test_login_invalid_user(self):
        """Test login with invalid credentials."""

        self.client.post("/api/register", json=self.test_user)

        response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": "wrongpassword"
        })

        self.assertEqual(response.status_code, 401)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "Invalid credentials.")

    def test_refresh_token(self):
        """Test token refresh."""

        self.client.post("/api/register", json=self.test_user)

        login_response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })

        refresh_token = login_response.json["refresh_token"]

        response = self.client.post("/api/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json)

    def test_logout_user(self):
        """Test user logout."""

        self.client.post("/api/register", json=self.test_user)

        login_response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })

        access_token = login_response.json["access_token"]

        response = self.client.post("/api/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "Successfully logged out.")

    def test_get_user_admin(self):
        """Test getting a user by ID with admin privileges."""

        self.client.post("/api/register", json=self.admin_user)

        admin_user = db.session.get(UserModel, 1 )
        admin_user.role = db.session.get(RoleModel, 1)
        db.session.commit()

        login_response = self.client.post("/api/login", json={
            "email": self.admin_user["email"],
            "password": self.admin_user["password"]
        })

        access_token = login_response.json["access_token"]
        response = self.client.get("/api/user/1", headers={
            "Authorization": f"Bearer {access_token}"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.json)
        self.assertEqual(response.json["email"], "test_admin@mail.com")
        self.assertIn("id", response.json)
        self.assertEqual(response.json["id"], 1)

    def test_delete_user_admin(self):
        """Test deleting a user by ID with admin privileges."""

        self.client.post("/api/register", json=self.admin_user)
        self.client.post("/api/register", json=self.test_user)

        admin_user = db.session.get(UserModel, 1 )
        admin_user.role = db.session.get(RoleModel, 1)
        db.session.commit()

        login_response = self.client.post("/api/login", json={
            "email": self.admin_user["email"],
            "password": self.admin_user["password"]
        })
        
        access_token = login_response.json["access_token"]

        response = self.client.delete(f"/api/user/2", headers={
            "Authorization": f"Bearer {access_token}"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "User deleted.")