import sqlite3
import os
from typing import List, Dict, Any, Optional
from automation.configuration.config import Config
from automation.utilities.logger import get_logger

logger = get_logger("DBClient")

# SQLite DB path relative to project root (matches DATABASE_URL in env)
_SQLITE_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "eqe_platform.db"
)


class DatabaseClient:
    """Database query execution client.

    Primary backend: SQLite (local development / CI).
    Optional backend: PostgreSQL (production / docker) via psycopg2.
    Falls back to SQLite automatically when PostgreSQL is unavailable.
    """

    def __init__(self, config: Config):
        self.config = config
        self.host = config.db_host
        self.port = config.db_port
        self.database = config.db_name
        self.user = config.db_user
        self.password = config.db_password

    # ------------------------------------------------------------------
    # SQLite backend (local / CI)
    # ------------------------------------------------------------------
    def _sqlite_execute(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query against the local SQLite database file."""
        db_path = os.path.normpath(_SQLITE_DB_PATH)
        if not os.path.exists(db_path):
            logger.warning(f"SQLite DB not found at {db_path}. Returning empty result.")
            return []

        # Translate PostgreSQL-style %s placeholders to SQLite ? placeholders
        sqlite_query = query.replace("%s", "?")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # enables dict-style access
        try:
            cursor = conn.execute(sqlite_query, params)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.info(f"SQLite query returned {len(result)} rows.")
            return result
        except Exception as e:
            logger.error(f"SQLite Query Error: {e}\nQuery: {sqlite_query}")
            raise
        finally:
            conn.close()

    def _sqlite_execute_statement(self, statement: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE against the local SQLite database."""
        db_path = os.path.normpath(_SQLITE_DB_PATH)
        sqlite_stmt = statement.replace("%s", "?")
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(sqlite_stmt, params)
            conn.commit()
            affected = cursor.rowcount
            logger.info(f"SQLite statement executed. Affected rows: {affected}")
            return affected
        except Exception as e:
            conn.rollback()
            logger.error(f"SQLite Statement Error: {e}")
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # PostgreSQL backend (production / docker)
    # ------------------------------------------------------------------
    def _get_pg_connection(self):
        try:
            import psycopg2
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password
            )
        except Exception as e:
            logger.info(f"PostgreSQL unavailable ({type(e).__name__}). Using SQLite fallback.")
            return None

    # ------------------------------------------------------------------
    # Public API (auto-selects backend)
    # ------------------------------------------------------------------
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executes a SQL SELECT query and returns rows as a list of dicts.

        Tries PostgreSQL first; falls back to SQLite automatically.
        """
        conn = self._get_pg_connection()
        if not conn:
            return self._sqlite_execute(query, params)

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
                logger.info(f"PostgreSQL query returned {len(result)} rows.")
                return result
        except Exception as e:
            logger.error(f"PostgreSQL Query Error: {e}")
            raise
        finally:
            conn.close()

    def execute_statement(self, statement: str, params: tuple = ()) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns affected row count."""
        conn = self._get_pg_connection()
        if not conn:
            return self._sqlite_execute_statement(statement, params)

        try:
            with conn.cursor() as cursor:
                cursor.execute(statement, params)
                conn.commit()
                affected = cursor.rowcount
                logger.info(f"PostgreSQL statement executed. Affected rows: {affected}")
                return affected
        except Exception as e:
            conn.rollback()
            logger.error(f"PostgreSQL Statement Error: {e}")
            raise
        finally:
            conn.close()
