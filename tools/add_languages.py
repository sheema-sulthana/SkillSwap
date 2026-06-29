import sqlite3

conn = sqlite3.connect("database/database.db")

cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE users
    ADD COLUMN languages TEXT DEFAULT ''
    """)
    print("SUCCESS: languages column added")

except Exception as e:
    print("ERROR:", e)

conn.commit()
conn.close()