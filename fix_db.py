import sqlite3

try:
    # Connect database
    conn = sqlite3.connect("hair.db")
    c = conn.cursor()

    # Add image column if not exists
    c.execute("ALTER TABLE users ADD COLUMN image TEXT")

    print("✅ Image column added successfully")

except sqlite3.OperationalError as e:
    print("⚠️ Column already exists or error:", e)

finally:
    conn.commit()
    conn.close()