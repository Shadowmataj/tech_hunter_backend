from test.base_test import BaseTest
from app.models import UserModel
from app.extensions import db
from app.schemas import UserSchema, UserRegisterSchema
from app.models.user import RoleModel


class UserTest(BaseTest):
    """Unit tests for the UserModel and its serialization/deserialization."""

    def setUp(self):
        """Set up test variables and initialize the database."""
        super().setUp()
        self.schema = UserSchema()
        self.register_schema = UserRegisterSchema()
        self.test_user = {
            "first_name": "Test_name",
            "last_name": "Test_lastname",
            "birth_date": "1990-01-01",
            "email": "test@mail.com",
            "password": "123456",
        }
        roles = [
            {"id": 0, "name": "admin"},
            {"id": 1, "name": "user"}
        ]
        for role_data in roles:
            role = RoleModel(**role_data)
            db.session.add(role)
        db.session.commit()

        user = self.register_schema.load(self.test_user)
        db.session.add(user)
        db.session.commit()


    def test_unit_register_user(self):
        """Test user registration and database insertion."""

        fetched_user = UserModel.query.filter_by(email="test@mail.com").first()
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.first_name, "Test_name")
        self.assertEqual(fetched_user.last_name, "Test_lastname")
        self.assertEqual(str(fetched_user.birth_date), "1990-01-01")
        self.assertEqual(fetched_user.email, "test@mail.com")
        self.assertNotEqual(fetched_user.password, "123456")
        self.assertEqual(fetched_user.role.name, "user")

        serialized_user = self.schema.dump(fetched_user)
        self.assertIn("id", serialized_user)
        self.assertEqual(serialized_user["first_name"], "Test_name")
        self.assertEqual(serialized_user["last_name"], "Test_lastname")
        self.assertEqual(serialized_user["birth_date"], "1990-01-01")
        self.assertEqual(serialized_user["email"], "test@mail.com")
        self.assertNotIn("password", serialized_user)
        self.assertEqual(serialized_user["role"]["name"], "user")


    def test_unit_put_user(self):
        """Test updating a user's information."""

        expected_email = "new_test@mail.com"

        fetched_user = UserModel.query.filter_by(email="test@mail.com").first()
        fetched_user.email = expected_email
        
        new_role = db.session.get(RoleModel, 1)
        fetched_user.role = new_role
        db.session.commit()

        updated_user = UserModel.query.filter_by(email=expected_email).first()

        serialized_user = self.schema.dump(updated_user)
        self.assertEqual(serialized_user["email"], expected_email)

    def test_unit_delete_user(self):
        """Test deleting a user from the database."""

        fetched_user = UserModel.query.filter_by(email="test@mail.com").first()
        db.session.delete(fetched_user)
        db.session.commit()

        deleted_user = UserModel.query.filter_by(email="test@mail.com").first()
        self.assertIsNone(deleted_user)
