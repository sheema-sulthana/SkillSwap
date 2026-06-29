
import sqlite3

conn = sqlite3.connect("database/database.db")

cursor = conn.cursor()

try:

    cursor.execute("""
    ALTER TABLE messages
    ADD COLUMN voice_file TEXT
    """)

    conn.commit()

    print("voice_file column added successfully")

except Exception as e:

    print("Error:", e)

conn.close()
