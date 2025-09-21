import unittest
from app import create_app, db
from sqlalchemy import event, text

class BaseTest(unittest.TestCase):
    """Base class for unit tests."""

    @classmethod
    def setUpClass(cls):
        """Runs once before any test in the class."""

        db_url = "postgresql+psycopg2://test:test@localhost:5433/test_db"

        cls.app = create_app(db_url=db_url)
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        db.drop_all()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests in the class."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Runs before each test."""
            
        # Clear data from all tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
            if table.name in ["products", "users"]:  # agrega tus tablas con ID serial
                db.session.execute(text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH 1"))
        db.session.commit()

        # Use nested transactions for test isolation
        self.transaction = db.session.begin_nested()

        @event.listens_for(db.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                session.begin_nested()
        
    def tearDown(self):
        """Runs after each test."""
        db.session.rollback()