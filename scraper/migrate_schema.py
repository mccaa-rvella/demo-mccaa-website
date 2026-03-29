"""
MCCAA Knowledge Base Schema Migration
Run this script to add taxonomy columns to the documents table
and create the sectors reference table.
"""
import psycopg2
import os

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "mysecretpassword")
DB_NAME = os.getenv("DB_NAME", "mccaa_website")

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
cur = conn.cursor()

print("=== Phase A: Schema Migration ===\n")

# 1. Add new columns to documents table
print("Adding taxonomy columns to documents...")
migrations = [
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS sector TEXT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS pillar TEXT DEFAULT 'technical'",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS roles TEXT[] DEFAULT '{}'",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS topic_tags TEXT[] DEFAULT '{}'",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS scope TEXT DEFAULT 'sector-specific'",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS slug TEXT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS legal_basis TEXT",
]
for sql in migrations:
    try:
        cur.execute(sql)
        print(f"  ✓ {sql.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]}")
    except Exception as e:
        print(f"  ⚠ Skipped: {e}")
        conn.rollback()

# Make slug unique (may already exist)
try:
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_slug ON documents(slug) WHERE slug IS NOT NULL")
    print("  ✓ slug unique index")
except Exception as e:
    print(f"  ⚠ slug index: {e}")
    conn.rollback()

conn.commit()

# 2. Create sectors reference table
print("\nCreating sectors table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS sectors (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        showcase BOOLEAN DEFAULT FALSE,
        sort_order INTEGER DEFAULT 99
    )
""")
conn.commit()
print("  ✓ sectors table created")

# 3. Populate sectors
print("\nPopulating sectors...")
sectors = [
    ("Toys", "toys", True, 1),
    ("Electrical & Electronic Equipment", "electrical", True, 2),
    ("General Consumer Products", "consumer-products", True, 3),
    ("Machinery", "machinery", False, 4),
    ("Construction Products", "construction", False, 5),
    ("Medical Devices", "medical-devices", False, 6),
    ("Personal Protective Equipment (PPE)", "ppe", False, 7),
    ("Radio Equipment", "radio-equipment", False, 8),
    ("Gas Appliances", "gas-appliances", False, 9),
    ("Pressure Equipment", "pressure-equipment", False, 10),
    ("Measuring Instruments", "measuring-instruments", False, 11),
    ("Pyrotechnics", "pyrotechnics", False, 12),
]

for name, slug, showcase, sort_order in sectors:
    try:
        cur.execute(
            "INSERT INTO sectors (name, slug, showcase, sort_order) VALUES (%s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            (name, slug, showcase, sort_order)
        )
        print(f"  ✓ {name} {'⭐' if showcase else ''}")
    except Exception as e:
        print(f"  ⚠ {name}: {e}")

conn.commit()

# 4. Verify
cur.execute("SELECT count(*) FROM sectors")
print(f"\n✅ Migration complete. {cur.fetchone()[0]} sectors in database.")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"Documents columns: {', '.join(cols)}")

cur.close()
conn.close()
