import sqlite3

conn = sqlite3.connect("database/database.db")

cursor = conn.cursor()

cursor.execute("""
DELETE FROM connections
WHERE id NOT IN (
    SELECT MIN(id)
    FROM connections
    GROUP BY user1_id, user2_id
)
""")

conn.commit()

print("✅ Duplicate connections removed successfully!")

conn.close()