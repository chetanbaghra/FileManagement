"""
db.py — Database Connection & Table Setup
──────────────────────────────────────────
Edit ONLY this file to change DB settings.
All modules import get_db() from here.

TO CHANGE PASSWORD : edit DB_CONFIG['password'] below
TO ADD A NEW TABLE : add a CREATE TABLE block in init_db()
                     then restart the server — table is created automatically
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# ── EDIT THESE IF NEEDED ──────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "lt_manager",
    "user":     "lt_user",
    "password": "lt_password123",   # ← change this if you change your DB password
}
# ─────────────────────────────────────────────────────────────────────────────


@contextmanager
def get_db():
    """
    Use like this in any module:
        from db import get_db
        with get_db() as (conn, cur):
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    """
    Creates all tables if they don't exist.
    Called once on server startup.
    Safe to run multiple times — never deletes existing data.

    TO ADD A NEW TABLE IN FUTURE:
        1. Add a CREATE TABLE IF NOT EXISTS block below
        2. Restart the server
        3. Table is created automatically
    """
    with get_db() as (conn, cur):

        # ── SETTINGS ─────────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id         INTEGER PRIMARY KEY DEFAULT 1,
                data       JSONB    NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT NOW(),
                CHECK (id = 1)
            )
        """)
        cur.execute("INSERT INTO settings (id, data) VALUES (1, '{}') ON CONFLICT DO NOTHING")

        # ── BUDGET HEADS ─────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS budget_heads (
                id         SERIAL PRIMARY KEY,
                type       VARCHAR(10)  NOT NULL,
                label      VARCHAR(100) NOT NULL,
                bh         VARCHAR(100) NOT NULL,
                proj       VARCHAR(200),
                hoa        VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── SUPPLIERS ────────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id         SERIAL PRIMARY KEY,
                name       VARCHAR(200) NOT NULL,
                contact    VARCHAR(100),
                email      VARCHAR(200),
                address    TEXT,
                gstin      VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── USERS ────────────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                name          VARCHAR(100) NOT NULL,
                username      VARCHAR(50)  NOT NULL UNIQUE,
                password_hash VARCHAR(200),
                role          VARCHAR(20)  DEFAULT 'user',
                division      VARCHAR(100),
                created_at    TIMESTAMP DEFAULT NOW(),
                last_login    TIMESTAMP
            )
        """)
        cur.execute("""
            INSERT INTO users (name, username, password_hash, role)
            VALUES ('Admin', 'admin', 'admin123', 'admin')
            ON CONFLICT DO NOTHING
        """)

        # ── WORK ORDERS ──────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id             SERIAL PRIMARY KEY,
                ref_no         VARCHAR(100),
                work_name      VARCHAR(500),
                div_code       VARCHAR(50),
                financial_year VARCHAR(20),
                serial_no      VARCHAR(20),
                budget_type    VARCHAR(20),
                budget_head    VARCHAR(200),
                estimated_cost NUMERIC(15,2),
                delivery_value VARCHAR(20),
                delivery_unit  VARCHAR(20),
                form_data      JSONB NOT NULL DEFAULT '{}',
                progress       JSONB NOT NULL DEFAULT '{}',
                created_by     INTEGER REFERENCES users(id),
                saved_at       TIMESTAMP DEFAULT NOW(),
                updated_at     TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── ACTIVITY LOG ─────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wo_activity_log (
                id         SERIAL PRIMARY KEY,
                wo_id      INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                user_name  VARCHAR(100),
                action     VARCHAR(100) NOT NULL,
                detail     TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── FILE ATTACHMENTS ─────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id          SERIAL PRIMARY KEY,
                wo_id       INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                category    VARCHAR(50),
                file_name   VARCHAR(300) NOT NULL,
                file_path   VARCHAR(500) NOT NULL,
                file_size   INTEGER,
                mime_type   VARCHAR(100),
                notes       TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── COMPARATIVE STATEMENT ─────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comparative_statements (
                id          SERIAL PRIMARY KEY,
                wo_id       INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                bid_data    JSONB NOT NULL DEFAULT '{}',
                recommended JSONB,
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT NOW(),
                updated_at  TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── PAYMENT DOCUMENTS ────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_documents (
                id         SERIAL PRIMARY KEY,
                wo_id      INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                doc_type   VARCHAR(50)  NOT NULL,
                doc_data   JSONB NOT NULL DEFAULT '{}',
                status     VARCHAR(30)  DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── DELIVERY EXTENSIONS ──────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS delivery_extensions (
                id            SERIAL PRIMARY KEY,
                wo_id         INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                original_date DATE,
                extended_date DATE,
                reason        TEXT,
                approved_by   VARCHAR(100),
                created_at    TIMESTAMP DEFAULT NOW()
            )
        """)

        # ── EMAIL REMINDERS ──────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_reminders (
                id          SERIAL PRIMARY KEY,
                wo_id       INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
                stage       VARCHAR(50),
                remind_date DATE,
                sent        BOOLEAN   DEFAULT FALSE,
                sent_at     TIMESTAMP,
                recipients  TEXT
            )
        """)

        # ── SEED DEFAULT DATA ─────────────────────────────────────────────────
        cur.execute("SELECT COUNT(*) as c FROM budget_heads")
        if cur.fetchone()['c'] == 0:
            cur.execute("""
                INSERT INTO budget_heads (type, label, bh, proj, hoa) VALUES
                ('Revenue', 'M&R - Civil',        '2215/FA/M&R/Civil', 'Maintenance & Repairs - Civil Works',  '2215-01-051-00-00'),
                ('Revenue', 'M&R - Electrical',   '2215/FA/M&R/Elec',  'Maintenance & Repairs - Electrical',   '2215-01-052-00-00'),
                ('Capital', 'New Construction',   '4216/FA/NC/Civil',  'New Construction Works',               '4216-01-051-00-00'),
                ('Capital', 'Equipment Purchase', '4216/FA/EP/Mech',   'Equipment & Machinery',                '4216-01-053-00-00')
            """)

        cur.execute("SELECT COUNT(*) as c FROM suppliers")
        if cur.fetchone()['c'] == 0:
            cur.execute("""
                INSERT INTO suppliers (name) VALUES
                ('M/s ABC Fabricators'), ('M/s XYZ Engineering Works'),
                ('M/s PQR Metal Works'), ('M/s LMN Steel Fabricators'),
                ('M/s DEF Industrial Works')
            """)

    print("✅ All database tables ready")
