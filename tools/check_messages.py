import sqlite3

conn = sqlite3.connect("database/database.db")
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute("""
SELECT *
FROM messages
ORDER BY id DESC
LIMIT 10
""")

rows = cursor.fetchall()

for row in rows:
    print(dict(row))

conn.close()
