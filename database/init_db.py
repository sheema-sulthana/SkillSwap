import sqlite3

DATABASE = "database/database.db"

conn = sqlite3.connect(DATABASE)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,

    profile_pic TEXT DEFAULT '',

    bio TEXT DEFAULT '',

    teach_skills TEXT DEFAULT '',

    learn_skills TEXT DEFAULT '',

    languages TEXT DEFAULT ''

)
""")
print("Database initialized successfully")
cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sender_id INTEGER NOT NULL,

    receiver_id INTEGER NOT NULL,

    type TEXT NOT NULL,

    status TEXT DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS connections (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user1_id INTEGER NOT NULL,

    user2_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sender_id INTEGER NOT NULL,

    receiver_id INTEGER NOT NULL,

    message TEXT,

    file_path TEXT,

    file_name TEXT,
    voice_file TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS blocked_users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    blocker_id INTEGER NOT NULL,

    blocked_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    event_date TEXT NOT NULL,

    event_time TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS learning_tracks (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    teacher_id INTEGER NOT NULL,

    learner_id INTEGER NOT NULL,

    skill_name TEXT NOT NULL,

    total_sessions INTEGER DEFAULT 10,

    completed_sessions INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS video_call_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    caller_id INTEGER,

    receiver_id INTEGER,

    action TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
cursor.execute("""

CREATE TABLE IF NOT EXISTS sessions (

id INTEGER PRIMARY KEY AUTOINCREMENT,

teacher_id INTEGER NOT NULL,

skill TEXT NOT NULL,

title TEXT NOT NULL,

description TEXT,

session_date TEXT NOT NULL,

session_time TEXT NOT NULL,

duration INTEGER DEFAULT 60,
               
meeting_link TEXT,
               
status TEXT DEFAULT 'scheduled',

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS session_participants (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    learner_id INTEGER NOT NULL,

    status TEXT DEFAULT 'joined',

    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(session_id) REFERENCES sessions(id),

    FOREIGN KEY(learner_id) REFERENCES users(id)

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS session_members (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    student_id INTEGER NOT NULL,

    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")
conn.commit()
conn.close()

