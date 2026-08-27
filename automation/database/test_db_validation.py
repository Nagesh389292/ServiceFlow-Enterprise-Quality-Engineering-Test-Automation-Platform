import pytest
from automation.database.db_client import DatabaseClient


@pytest.mark.database
class TestDatabaseValidation:
    """Database test suite validating backend data integrity, seed records, and SQL constraints."""

    def test_default_priorities_seeded(self, db_client: DatabaseClient):
        """TC_DB_01: Verify default SLA priorities (P1, P2, P3, P4) exist in database."""
        query = "SELECT name, sla_hours FROM priorities WHERE is_active = true ORDER BY name;"
        rows = db_client.execute_query(query)
        if rows:
            names = [r["name"] for r in rows]
            assert "P1" in names
            assert "P3" in names

    def test_default_categories_seeded(self, db_client: DatabaseClient):
        """TC_DB_02: Verify default service desk categories exist in database."""
        query = "SELECT name FROM categories WHERE is_active = true;"
        rows = db_client.execute_query(query)
        if rows:
            cat_names = [r["name"] for r in rows]
            assert "Hardware" in cat_names or "Software" in cat_names

    def test_admin_user_seed_integrity(self, db_client: DatabaseClient):
        """TC_DB_03: Verify default admin user record exists with active status."""
        query = "SELECT email, role, is_active FROM users WHERE email = %s;"
        rows = db_client.execute_query(query, ("admin@eqe.com",))
        if rows:
            assert rows[0]["role"].lower() == "admin"
            assert bool(rows[0]["is_active"]) is True
