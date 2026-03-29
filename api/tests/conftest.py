import os

# Set test DB env vars before any api modules are imported (settings is a singleton)
TEST_DB_NAME = "mccaa_website_test"
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["DB_PORT"] = os.environ.get("DB_PORT", "5434")

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5434"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "mysecretpassword"),
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    cur.close()
    conn.close()

    from api.db import ensure_schema
    ensure_schema()
    yield

    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5434"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "mysecretpassword"),
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cur.close()
    conn.close()


@pytest.fixture
def db_cursor():
    from api.db import get_connection
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    yield cur
    conn.rollback()
    cur.close()
    conn.close()
