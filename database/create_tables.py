import sqlite3

conn = sqlite3.connect("database/database.db")
cursor = conn.cursor()

# Connection Requests
cursor.execute("""
CREATE TABLE IF NOT EXISTS connection_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    status TEXT DEFAULT 'pending'
)
""")

# Accepted Connections
cursor.execute("""
CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER,
    user2_id INTEGER
)
""")

# Messages
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
CREATE TABLE IF NOT EXISTS video_call_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    caller_id INTEGER,

    receiver_id INTEGER,

    action TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);
conn.commit()
conn.close()

print("Tables Created Successfully")