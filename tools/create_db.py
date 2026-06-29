import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

# Create table

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    username TEXT,

    teaches TEXT,

    learns TEXT,

    bio TEXT

)
""")

# Clear old data (optional)

cursor.execute("DELETE FROM users")

# Sample Users

users = [

(
"Aarav Sharma",
"aarav01",
"Python,Web Development",
"Graphic Design",
"Web developer and tech enthusiast."
),

(
"Priya Singh",
"priya_sg",
"UI/UX Design",
"Photography",
"Creative designer who loves minimalism."
),

(
"Kabir Mehta",
"kabir",
"AI,Web Development",
"Cooking",
"Full-stack developer and AI enthusiast."
),

(
"Rahul Verma",
"rahulv",
"Cooking",
"Python",
"Passionate home chef."
),

(
"Sneha Reddy",
"sneha",
"Photography",
"AI",
"Photography lover and traveler."
),

(
"Aditya Kumar",
"aditya",
"Chess",
"Web Development",
"National level chess player."
),

(
"Ananya Sharma",
"ananya",
"Graphic Design",
"Python",
"Freelance graphic designer."
),

(
"Rohan Gupta",
"rohan",
"Video Editing",
"Photography",
"Content creator and editor."
)

]

cursor.executemany("""

INSERT INTO users(

name,
username,
teaches,
learns,
bio

)

VALUES(?,?,?,?,?)

""", users)

conn.commit()

conn.close()

print("Sample Users Added Successfully")