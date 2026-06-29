import sqlite3
import os
from flask import request
import calendar as pycalendar
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)
from database.db import get_connection
from datetime import timedelta

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
load_dotenv()
oauth = OAuth(app)
google = oauth.register(

    name='google',

    client_id=os.getenv("GOOGLE_CLIENT_ID"),

    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),

    server_metadata_url=
    "https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={
        "scope": "openid email profile"
    }

)
app.secret_key = os.getenv("SECRET_KEY")
@app.route('/')
def home():
    return render_template('home/index.html')

@app.route('/about')
def about():
    return render_template('home/about.html')
@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        return render_template(
            'home/contact.html',
            success=True
        )

    return render_template(
        'home/contact.html',
        success=False
    )

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = get_connection()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE email=? AND password=?
            """,
            (email,password)
        ).fetchone()

        conn.close()

        if user:

            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']

            return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (name,email,password)
                VALUES(?,?,?)
                """,
                (name,email,password)
            )

            conn.commit()

            return redirect('/login')

        except:

            return "Email already exists"

        finally:

            conn.close()

    return render_template('auth/signup.html')
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    # Current User
    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (session['user_id'],)
    ).fetchone()

    # Skills Offered Count
    skills_offered = len(
        [
            skill.strip()
            for skill in user['teach_skills'].split(',')
            if skill.strip()
        ]
    ) if user['teach_skills'] else 0

    # Skills Learning Count
    skills_learning = len(
        [
            skill.strip()
            for skill in user['learn_skills'].split(',')
            if skill.strip()
        ]
    ) if user['learn_skills'] else 0

    # Connections Count
    connections = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM connections
        WHERE
        user1_id=?
        OR user2_id=?
        """,
        (
            session['user_id'],
            session['user_id']
        )
    ).fetchone()

    total_connections = connections['total']

    # Matches Count
    current_teach_skills = (
        user['teach_skills'].split(',')
        if user['teach_skills']
        else []
    )

    users = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id != ?
        """,
        (session['user_id'],)
    ).fetchall()

    matched_users = []

    for other_user in users:

        learn_skills = (
            other_user['learn_skills'].split(',')
            if other_user['learn_skills']
            else []
        )

        if any(
            skill.strip() in
            [x.strip() for x in learn_skills]
            for skill in current_teach_skills
        ):
            matched_users.append(other_user)

    total_matches = len(matched_users)

    # Learning Progress (ONLY skills user is learning)
    learning_tracks = conn.execute(
        """
        SELECT *
        FROM learning_tracks
        WHERE learner_id=?
        """,
        (session['user_id'],)
    ).fetchall()

    # Achievement Count
    total_completed = sum(
        track['completed_sessions']
        for track in learning_tracks
    )

    earned_badges = 0

    if total_completed >= 1:
        earned_badges += 1

    if total_completed >= 5:
        earned_badges += 1

    if total_completed >= 10:
        earned_badges += 1

    if total_connections >= 3:
        earned_badges += 1

    if len(learning_tracks) >= 3:
        earned_badges += 1

    # Notifications
    notifications = conn.execute(
        """
        SELECT notifications.*, users.name
        FROM notifications
        JOIN users
        ON notifications.sender_id = users.id
        WHERE notifications.receiver_id=?
        AND notifications.status='pending'
        ORDER BY notifications.created_at DESC
        """,
        (session['user_id'],)
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard/dashboard.html',

        user=user,

        notifications=notifications,
        notifications_count=len(notifications),

        skills_offered=skills_offered,
        skills_learning=skills_learning,

        total_connections=total_connections,
        total_matches=total_matches,

        learning_tracks=learning_tracks,

        earned_badges=earned_badges,

        active_page='dashboard'
    )
@app.route('/users')
def users():

    conn = get_connection()

    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()

    conn.close()

    return str([dict(x) for x in users])
@app.route('/google-login')
def google_login():

    redirect_uri = url_for(
        'google_authorized',
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )
@app.route('/google-authorized')
def google_authorized():

    token = google.authorize_access_token()

    user_info = google.get("userinfo").json()

    email = user_info["email"]
    name = user_info["name"]
    picture = user_info["picture"]

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email=?
        """,
        (email,)
    ).fetchone()

    if not existing:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (name,email,password,profile_pic)
            VALUES(?,?,?,?)
            """,
            (
                name,
                email,
                "google_login",
                picture
            )
        )

        conn.commit()

        user_id = cursor.lastrowid

    else:

        user_id = existing["id"]

    conn.close()

    session["user_id"] = user_id
    session["name"] = name
    session["email"] = email
    session["profile_pic"] = picture

    session.permanent = True
    session.modified = True

    response = redirect(url_for("dashboard"))
    response.headers["Cache-Control"] = "no-store"

    return response
@app.route('/save-profile', methods=['POST'])
def save_profile():

    if 'user_id' not in session:
        return redirect('/login')

    bio = request.form.get('bio','')

    teach_skills = ",".join(
        request.form.getlist('teach_skills')
    )

    learn_skills = ",".join(
        request.form.getlist('learn_skills')
    )

    languages = ",".join(
        request.form.getlist('languages')
    )

    conn = get_connection()

    conn.execute(
        """
        UPDATE users
        SET bio=?,
            teach_skills=?,
            learn_skills=?,
            languages=?
        WHERE id=?
        """,
        (
            bio,
            teach_skills,
            learn_skills,
            languages,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/chat')
def chat():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    connections = conn.execute(
        """
        SELECT DISTINCT users.*
        FROM users
        JOIN connections
        ON (
            users.id = connections.user1_id
            OR
            users.id = connections.user2_id
        )
        WHERE (
            connections.user1_id = ?
            OR
            connections.user2_id = ?
        )
        AND users.id != ?
        """,
        (
            session['user_id'],
            session['user_id'],
            session['user_id']
        )
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard/chat.html',
        connections=connections,
        active_page='chat'
    )
@app.route('/chat/<int:user_id>')
def chat_room(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    receiver = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (user_id,)
    ).fetchone()

    messages = conn.execute(
        """
        SELECT *
        FROM messages
        WHERE
        (
            sender_id=? AND receiver_id=?
        )
        OR
        (
            sender_id=? AND receiver_id=?
        )
        ORDER BY created_at
        """,
        (
            session['user_id'],
            user_id,
            user_id,
            session['user_id']
        )
    ).fetchall()
    call_logs = conn.execute(
    """
    SELECT *
    FROM video_call_logs
    WHERE
    (
        caller_id=? AND receiver_id=?
    )
    OR
    (
        caller_id=? AND receiver_id=?
    )
    ORDER BY created_at ASC
    """,
    (
        session['user_id'],
        user_id,
        user_id,
        session['user_id']
    )
).fetchall()
    conn.close()

    return render_template(
    'dashboard/chat_room.html',
    receiver=receiver,
    messages=messages,
    call_logs=call_logs,
    active_page='chat'
)
@app.route('/send-message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):

    if 'user_id' not in session:
        return redirect('/login')

    message = request.form.get('message')

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO messages
        (
            sender_id,
            receiver_id,
            message
        )
        VALUES(?,?,?)
        """,
        (
            session['user_id'],
            receiver_id,
            message
        )
    )

    conn.commit()
    conn.close()

    return redirect(f'/chat/{receiver_id}')
@app.route('/community')
def community():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    users = conn.execute("""
        SELECT *
        FROM users
        WHERE id != ?
        ORDER BY id DESC
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template(
    'dashboard/community.html',
    users=users,
    active_page='community'
)
@app.route('/calendar')
def learning_calendar():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()


    sessions = conn.execute(

"""
SELECT

    sessions.*,
    users.name AS teacher_name,
    users.profile_pic

FROM session_participants

JOIN sessions
ON sessions.id = session_participants.session_id

JOIN users
ON users.id = sessions.teacher_id

WHERE session_participants.learner_id = ?

ORDER BY sessions.session_date

""",

(session['user_id'],)

).fetchall()


    conn.close()



    events=[]

    for s in sessions:
       events.append({
        'id': s['id'],
        'title': s['title'],
        'start': s['session_date'],
        'color': '#38bdf8'
    })
    for s in sessions:
      return render_template(

        'dashboard/calendar.html',

        sessions=sessions,

        events=events,

        active_page='calendar'

    )
@app.route('/progress')
def progress():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    learning_tracks = conn.execute("""
SELECT
    lt.*,
    u.name AS teacher_name
FROM learning_tracks lt
JOIN users u
ON lt.teacher_id = u.id
WHERE lt.learner_id=?
""",
(session['user_id'],)
).fetchall()

    teaching_tracks = conn.execute("""
SELECT
    lt.*,
    u.name AS learner_name
FROM learning_tracks lt
JOIN users u
ON lt.learner_id = u.id
WHERE lt.teacher_id=?
""",
(session['user_id'],)
).fetchall()
    conn.close()

    return render_template(
        'dashboard/progress.html',
        learning_tracks=learning_tracks,
        teaching_tracks=teaching_tracks,
        active_page='progress'
    )
@app.route('/complete-session/<int:track_id>')
def complete_session(track_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    conn.execute("""
    UPDATE learning_tracks
    SET completed_sessions =
        completed_sessions + 1
    WHERE id=?
    """, (track_id,))

    conn.commit()
    conn.close()

    return redirect('/progress')
@app.route('/achievements')
def achievements():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    tracks = conn.execute("""
    SELECT *
    FROM learning_tracks
    WHERE
    teacher_id=?
    OR learner_id=?
    """,
    (
        session['user_id'],
        session['user_id']
    )
    ).fetchall()

    total_completed = sum(
        track['completed_sessions']
        for track in tracks
    )

    connections = conn.execute("""
    SELECT COUNT(*) AS total
    FROM connections
    WHERE
    user1_id=?
    OR user2_id=?
    """,
    (
        session['user_id'],
        session['user_id']
    )
    ).fetchone()

    badges = [

        {
            "title": "First Session",
            "icon": "🥉",
            "description": "Complete your first session",
            "unlocked": total_completed >= 1
        },

        {
            "title": "Consistent Learner",
            "icon": "🥈",
            "description": "Complete 5 sessions",
            "unlocked": total_completed >= 5
        },

        {
            "title": "Skill Master",
            "icon": "🥇",
            "description": "Complete 10 sessions",
            "unlocked": total_completed >= 10
        },

        {
            "title": "Community Connector",
            "icon": "🤝",
            "description": "Connect with 3 users",
            "unlocked": connections['total'] >= 3
        },

        {
            "title": "Multi Skill Learner",
            "icon": "📚",
            "description": "Have 3 learning tracks",
            "unlocked": len(tracks) >= 3
        }

    ]

    earned_badges = len(
        [b for b in badges if b['unlocked']]
    )

    conn.close()

    return render_template(
        'dashboard/achievements.html',
        badges=badges,
        earned_badges=earned_badges,
        total_completed=total_completed,
        total_connections=connections['total'],
        active_page='achievements'
    )

@app.route('/profile')
def profile():
    return render_template(
    'dashboard/profile.html',
    active_page='profile'
)
@app.route('/edit-profile')
def edit_profile():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (session['user_id'],)
    ).fetchone()

    conn.close()

    return render_template(
    'dashboard/edit_profile.html',
    user=user,
    active_page='profile'
)
@app.route('/user-profile/<int:user_id>')
def user_profile(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not user:
        return "User not found"

    return render_template(
    'dashboard/community.html',
    users=users,
    active_page='community'
)
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')
@app.route('/matches')
def matches():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    current_user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    teach_skills = (
        current_user['teach_skills'].split(',')
        if current_user['teach_skills']
        else []
    )

    users = conn.execute(
        "SELECT * FROM users WHERE id != ?",
        (session['user_id'],)
    ).fetchall()

    matched_users = []

    for user in users:

        learn_skills = (
            user['learn_skills'].split(',')
            if user['learn_skills']
            else []
        )

        if any(skill in learn_skills for skill in teach_skills):
            matched_users.append(user)

    pending_requests = conn.execute(
        """
        SELECT receiver_id
        FROM notifications
        WHERE sender_id=?
        AND status='pending'
        """,
        (session['user_id'],)
    ).fetchall()

    pending_ids = [
        x['receiver_id']
        for x in pending_requests
    ]
    connections = conn.execute(
    """
    SELECT *
    FROM connections
    """
).fetchall()

    connected_ids = []
    for connection in connections:

     if connection['user1_id'] == session['user_id']:
        connected_ids.append(connection['user2_id'])
     elif connection['user2_id'] == session['user_id']:
        connected_ids.append(connection['user1_id'])
    conn.close()

    return render_template(
    'dashboard/matches.html',
    matches=matched_users,
    pending_ids=pending_ids,
    connected_ids=connected_ids,
    active_page='matches'
)
@app.route('/send-request/<int:user_id>')
def send_request(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE sender_id=?
        AND receiver_id=?
        AND type='connection_request'
        AND status='pending'
        """,
        (
            session['user_id'],
            user_id
        )
    ).fetchone()

    if not existing:

        conn.execute(
            """
            INSERT INTO notifications
            (
                sender_id,
                receiver_id,
                type
            )
            VALUES(?,?,?)
            """,
            (
                session['user_id'],
                user_id,
                'connection_request'
            )
        )

        conn.commit()

    conn.close()

    return redirect('/matches')
@app.route('/check-notifications')
def check_notifications():

    conn = get_connection()

    notifications = conn.execute(
        """
        SELECT *
        FROM notifications
        """
    ).fetchall()

    conn.close()

    return str([dict(x) for x in notifications])
@app.route('/test')
def test():
    return "TEST WORKING"
@app.route('/notifications')
def notifications():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    notifications = conn.execute(
        """
        SELECT
            notifications.*,
            users.name
        FROM notifications
        JOIN users
        ON notifications.sender_id = users.id
        WHERE receiver_id = ?
        AND status = 'pending'
        ORDER BY created_at DESC
        """,
        (session['user_id'],)
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard/notifications.html',
        notifications=notifications,
        active_page='dashboard'
    )
@app.route('/accept-request/<int:notification_id>')
def accept_request(notification_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    notification = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE id=?
        """,
        (notification_id,)
    ).fetchone()

    if notification:

        existing_connection = conn.execute(
            """
            SELECT *
            FROM connections
            WHERE
            (
                user1_id=? AND user2_id=?
            )
            OR
            (
                user1_id=? AND user2_id=?
            )
            """,
            (
                notification['sender_id'],
                notification['receiver_id'],
                notification['receiver_id'],
                notification['sender_id']
            )
        ).fetchone()

        if not existing_connection:

            # Create connection
            conn.execute(
                """
                INSERT INTO connections
                (
                    user1_id,
                    user2_id
                )
                VALUES(?,?)
                """,
                (
                    notification['sender_id'],
                    notification['receiver_id']
                )
            )

            teacher = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id=?
                """,
                (notification['sender_id'],)
            ).fetchone()

            learner = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id=?
                """,
                (notification['receiver_id'],)
            ).fetchone()

            if teacher and learner:

                # Teacher → Learner tracks
                teacher_skills = (
                    teacher['teach_skills'].split(',')
                    if teacher['teach_skills']
                    else []
                )

                learner_skills = (
                    learner['learn_skills'].split(',')
                    if learner['learn_skills']
                    else []
                )

                for skill in teacher_skills:

                    skill = skill.strip()

                    if skill in [
                        s.strip()
                        for s in learner_skills
                    ]:

                        conn.execute(
                            """
                            INSERT INTO learning_tracks
                            (
                                teacher_id,
                                learner_id,
                                skill_name
                            )
                            VALUES(?,?,?)
                            """,
                            (
                                teacher['id'],
                                learner['id'],
                                skill
                            )
                        )

                # Learner → Teacher tracks
                reverse_teacher_skills = (
                    learner['teach_skills'].split(',')
                    if learner['teach_skills']
                    else []
                )

                reverse_learner_skills = (
                    teacher['learn_skills'].split(',')
                    if teacher['learn_skills']
                    else []
                )

                for skill in reverse_teacher_skills:

                    skill = skill.strip()

                    if skill in [
                        s.strip()
                        for s in reverse_learner_skills
                    ]:

                        conn.execute(
                            """
                            INSERT INTO learning_tracks
                            (
                                teacher_id,
                                learner_id,
                                skill_name
                            )
                            VALUES(?,?,?)
                            """,
                            (
                                learner['id'],
                                teacher['id'],
                                skill
                            )
                        )

        conn.execute(
            """
            UPDATE notifications
            SET status='accepted'
            WHERE id=?
            """,
            (notification_id,)
        )

    conn.commit()
    conn.close()

    return redirect('/dashboard')
@app.route('/reject-request/<int:notification_id>')
def reject_request(notification_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    conn.execute(
        """
        UPDATE notifications
        SET status='rejected'
        WHERE id=?
        """,
        (notification_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')
@app.route('/upload-file/<int:user_id>', methods=['POST'])
def upload_file(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    file = request.files.get('file')

    if file and file.filename:

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        file.save(filepath)

        conn = get_connection()

        conn.execute(
            """
            INSERT INTO messages
            (
                sender_id,
                receiver_id,
                message,
                file_path,
                file_name
            )
            VALUES(?,?,?,?,?)
            """,
            (
                session['user_id'],
                user_id,
                '',
                filepath,
                filename
            )
        )

        conn.commit()
        conn.close()

    return redirect(f'/chat/{user_id}')
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):

    return send_from_directory(
        'uploads',
        filename,
        as_attachment=False
    )
@app.route('/download/<path:filename>')
def download_file(filename):

    return send_from_directory(
        'uploads',
        filename,
        as_attachment=True
    )
@app.route('/upload-voice/<int:user_id>', methods=['POST'])
def upload_voice(user_id):

    if 'user_id' not in session:
        return '', 401

    voice = request.files.get('voice')

    if voice:

        filename = secure_filename(
            voice.filename
        )

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        voice.save(filepath)

        conn = get_connection()

        conn.execute(
    """
    INSERT INTO messages
    (
        sender_id,
        receiver_id,
        voice_file
    )
    VALUES(?,?,?)
    """,
    (
        session['user_id'],
        user_id,
        filename
    )
)


        conn.commit()
        conn.close()

    return '', 200
@app.route('/delete-chat/<int:user_id>')
def delete_chat(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM messages
        WHERE
        (
            sender_id=? AND receiver_id=?
        )
        OR
        (
            sender_id=? AND receiver_id=?
        )
        """,
        (
            session['user_id'],
            user_id,
            user_id,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/chat')
@app.route('/block-user/<int:user_id>')
def block_user(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT *
        FROM blocked_users
        WHERE blocker_id=?
        AND blocked_id=?
        """,
        (
            session['user_id'],
            user_id
        )
    ).fetchone()

    if not existing:

        conn.execute(
            """
            INSERT INTO blocked_users
            (
                blocker_id,
                blocked_id
            )
            VALUES(?,?)
            """,
            (
                session['user_id'],
                user_id
            )
        )

        conn.commit()

    conn.close()

    return redirect('/chat')
@app.route('/check-tracks')
def check_tracks():

    conn = get_connection()

    tracks = conn.execute(
        "SELECT * FROM learning_tracks"
    ).fetchall()

    conn.close()

    return str([dict(x) for x in tracks])
@app.route('/check-user-skills')
def check_user_skills():

    conn = get_connection()

    users = conn.execute("""
    SELECT
        id,
        name,
        teach_skills,
        learn_skills
    FROM users
    """).fetchall()

    conn.close()

    return str([dict(x) for x in users])
@app.route('/generate-tracks')
def generate_tracks():

    conn = get_connection()

    connections = conn.execute("""
    SELECT *
    FROM connections
    """).fetchall()

    for connection in connections:

        teacher = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (connection['user1_id'],)
        ).fetchone()

        learner = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (connection['user2_id'],)
        ).fetchone()

        teacher_skills = (
            teacher['teach_skills'].split(',')
            if teacher['teach_skills']
            else []
        )

        learner_skills = (
            learner['learn_skills'].split(',')
            if learner['learn_skills']
            else []
        )

        for skill in teacher_skills:

            if skill.strip() in [
                x.strip()
                for x in learner_skills
            ]:

                existing = conn.execute("""
                SELECT *
                FROM learning_tracks
                WHERE
                teacher_id=?
                AND learner_id=?
                AND skill_name=?
                """,
                (
                    teacher['id'],
                    learner['id'],
                    skill.strip()
                )
                ).fetchone()
                reverse_teacher_skills = (
    learner['teach_skills'].split(',')
    if learner['teach_skills']
    else []
)

    reverse_learner_skills = (
    teacher['learn_skills'].split(',')
    if teacher['learn_skills']
    else []
)

    for skill in reverse_teacher_skills:

       if skill.strip() in [
        x.strip()
        for x in reverse_learner_skills
    ]:

        existing = conn.execute("""
        SELECT *
        FROM learning_tracks
        WHERE
        teacher_id=?
        AND learner_id=?
        AND skill_name=?
        """,
        (
            learner['id'],
            teacher['id'],
            skill.strip()
        )
        ).fetchone()

        if not existing:

            conn.execute("""
            INSERT INTO learning_tracks
            (
                teacher_id,
                learner_id,
                skill_name
            )
            VALUES(?,?,?)
            """,
            (
                learner['id'],
                teacher['id'],
                skill.strip()
            ))

            if not existing:

                    conn.execute("""
                    INSERT INTO learning_tracks
                    (
                        teacher_id,
                        learner_id,
                        skill_name
                    )
                    VALUES(?,?,?)
                    """,
                    (
                        teacher['id'],
                        learner['id'],
                        skill.strip()
                    ))

    conn.commit()
    conn.close()

    return "Tracks Generated"
@app.route('/check-video-calls')
def check_video_calls():

    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM video_call_logs"
    ).fetchall()

    conn.close()

    return str([dict(x) for x in rows])
@app.route('/clear-tracks')
def clear_tracks():

    conn = get_connection()

    conn.execute(
        "DELETE FROM learning_tracks"
    )

    conn.commit()
    conn.close()

    return "Tracks Cleared"
@app.route('/rebuild-tracks')
def rebuild_tracks():

    conn = get_connection()

    conn.execute(
        "DELETE FROM learning_tracks"
    )

    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()

    for teacher in users:

        teacher_skills = (
            teacher['teach_skills'].split(',')
            if teacher['teach_skills']
            else []
        )

        for learner in users:

            if teacher['id'] == learner['id']:
                continue

            learner_skills = (
                learner['learn_skills'].split(',')
                if learner['learn_skills']
                else []
            )

            for skill in teacher_skills:

                if skill.strip() in [
                    x.strip()
                    for x in learner_skills
                ]:

                    conn.execute(
                        """
                        INSERT INTO learning_tracks
                        (
                            teacher_id,
                            learner_id,
                            skill_name
                        )
                        VALUES(?,?,?)
                        """,
                        (
                            teacher['id'],
                            learner['id'],
                            skill.strip()
                        )
                    )

    conn.commit()
    conn.close()

    return "Tracks Rebuilt Successfully"
@app.route('/call/<int:user_id>')
def start_call(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()
    room = (
    f"SkillSwapRoom_"
    f"{min(session['user_id'], user_id)}_"
    f"{max(session['user_id'], user_id)}"
)
    conn.execute(
        """
        INSERT INTO video_call_logs
        (
            caller_id,
            receiver_id,
            action
        )
        VALUES
        (?, ?, ?)
        """,
        (
            session['user_id'],
            user_id,
            'started'
        )
    )
    conn.execute(
    """
    INSERT INTO messages
    (
        sender_id,
        receiver_id,
        message
    )
    VALUES(?,?,?)
    """,
    (
        session['user_id'],
        user_id,
        f"VIDEO_CALL_INVITE::{room}"
    )
)
    conn.commit()
    conn.close()

    room = (
        f"SkillSwapRoom_"
        f"{min(session['user_id'], user_id)}_"
        f"{max(session['user_id'], user_id)}"
    )

    return redirect(
        f"https://meet.jit.si/{room}"
    )
@app.route('/sessions')
def sessions():

    conn = get_connection()
    conn.execute(
    """
    UPDATE notifications
    SET status='read'
    WHERE receiver_id=?
    AND (
        type='session_created'
        OR
        type='session_live'
    )
    """,
    (session['user_id'],)
)

    conn.commit()

    user = conn.execute(
        """
        SELECT teach_skills
        FROM users
        WHERE id=?
        """,
        (session['user_id'],)
    ).fetchone()

    user_id = session['user_id']


    teaching_sessions = conn.execute(
        """
        SELECT *
        FROM sessions
        WHERE teacher_id=?
        ORDER BY session_date
        """,
        (user_id,)
    ).fetchall()


    learning_sessions = conn.execute(
    """
    SELECT

        sessions.*,
        users.name AS teacher_name,
        users.profile_pic

    FROM session_participants

    JOIN sessions
    ON sessions.id = session_participants.session_id

    JOIN users
    ON users.id = sessions.teacher_id

    WHERE session_participants.learner_id = ?

    ORDER BY sessions.session_date
    """,
    (user_id,)
).fetchall()
    conn.close()


    skills = []

    if user and user['teach_skills']:
        skills = user['teach_skills'].split(',')


    return render_template(

        'dashboard/sessions.html',

        teaching_sessions=teaching_sessions,

        learning_sessions=learning_sessions,

        skills=skills,

        active_page='sessions'

    )

@app.route('/create_session', methods=['POST'])
def create_session():

    if 'user_id' not in session:
        return redirect('/login')


    skill = request.form['skill']

    title = request.form['title']

    session_date = request.form['session_date']

    session_time = request.form['session_time']

    duration = request.form['duration']

    import time

    room_name = f"skillswap-{int(time.time())}"

    meeting_link = f"https://meet.jit.si/{room_name}"

    conn = get_connection()


    conn.execute(

        """

        INSERT INTO sessions(

            teacher_id,

            skill,

            title,

            session_date,

            session_time,

            duration,

            meeting_link,

            status

        )

        VALUES(

            ?,?,?,?,?,?,?,?

        )

        """,

        (

            session['user_id'],

            skill,

            title,

            session_date,

            session_time,

            duration,

            meeting_link,

            'scheduled'

        )

    )
    session_id = conn.execute(

    "SELECT last_insert_rowid()"

).fetchone()[0]
    tracks=conn.execute(

"""

SELECT learner_id

FROM learning_tracks

WHERE teacher_id=?

AND skill_name=?

"""

,

(

session['user_id'],

skill

)

).fetchall()

    for t in tracks:
       conn.execute(

    """

    INSERT INTO session_participants(

        session_id,

        learner_id,

        status

    )

    VALUES(

        ?,?,'joined'

    )

    """,

    (

        session_id,

        t['learner_id']

    )

)


       conn.execute(

    """

    INSERT INTO notifications(

    sender_id,

    receiver_id,

    type

    )

    VALUES(

    ?,?,?

    )

    """

    ,

    (

    session['user_id'],

    t['learner_id'],

    'session_created'

    )

    )
    conn.commit()

    conn.close()


    return redirect('/sessions')
@app.route('/start_session/<int:id>')
def start_session(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    sess = conn.execute(
        """
        SELECT *
        FROM sessions
        WHERE id=?
        """,
        (id,)
    ).fetchone()

    conn.execute(
        """
        UPDATE sessions
        SET status='live'
        WHERE id=?
        """,
        (id,)
    )
    learners = conn.execute(
    """
    SELECT learner_id
    FROM session_participants
    WHERE session_id=?
    """,
    (id,)
).fetchall()
    learners = conn.execute(
        """
        SELECT learner_id
        FROM session_participants
        WHERE session_id=?
        """,
        (id,)
    ).fetchall()

    for learner in learners:

        conn.execute(
            """
            INSERT INTO notifications
            (
                sender_id,
                receiver_id,
                type
            )
            VALUES(?,?,?)
            """,
            (
                session['user_id'],
                learner['learner_id'],
                'session_live'
            )
        )

    conn.commit()
    conn.close()

    return redirect(sess['meeting_link'])
@app.route('/end_session/<int:id>')
def end_session(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()

    conn.execute(
        """
        UPDATE sessions
        SET status='completed'
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect('/sessions')
    return "Coming Soon"
if __name__ == "__main__":
    app.run(
    host="0.0.0.0",
    port=5000,
    debug=False
)