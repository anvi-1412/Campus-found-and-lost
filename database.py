import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash
from config import Config

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            db_path = current_app.config.get('DATABASE_PATH', Config.DATABASE_PATH)
        except RuntimeError:
            db_path = Config.DATABASE_PATH

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries or a single row."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    """Executes a modification query and returns the last inserted rowid."""
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

def init_db(app=None):
    """Initializes database tables and default sample data."""
    try:
        db_path = app.config.get('DATABASE_PATH', Config.DATABASE_PATH) if app else (current_app.config.get('DATABASE_PATH', Config.DATABASE_PATH) if current_app else Config.DATABASE_PATH)
        upload_folder = app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER) if app else (current_app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER) if current_app else Config.UPLOAD_FOLDER)
    except RuntimeError:
        db_path = Config.DATABASE_PATH
        upload_folder = Config.UPLOAD_FOLDER

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL CHECK(item_type IN ('lost', 'found')),
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            event_date DATE NOT NULL,
            image_path TEXT,
            status TEXT NOT NULL CHECK(status IN ('Lost', 'Found', 'Claim Pending', 'Returned', 'Closed')),
            custody_info TEXT,
            contact_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Claims table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            claimer_id INTEGER NOT NULL,
            proof_description TEXT NOT NULL,
            proof_image TEXT,
            contact_phone TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
            admin_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
            FOREIGN KEY (claimer_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Activity logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        );
    """)

    conn.commit()

    # Seed Admin and Demo Students if no users exist
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        admin_pass = generate_password_hash("AdminPassword123!")
        alex_pass = generate_password_hash("StudentPassword123!")
        sarah_pass = generate_password_hash("StudentPassword123!")

        cursor.execute("""
            INSERT INTO users (name, email, student_id, department, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Campus Safety Admin',
            'admin@campus.edu',
            'ADMIN-001',
            'Campus Safety & Security',
            '+1 (555) 019-2834',
            admin_pass,
            'admin'
        ))
        admin_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (name, email, student_id, department, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Alex Rivera',
            'alex.student@campus.edu',
            'CS-2024-042',
            'Computer Science & Engineering',
            '+1 (555) 014-9921',
            alex_pass,
            'student'
        ))
        alex_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (name, email, student_id, department, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'Sarah Mitchell',
            'sarah.mitchell@campus.edu',
            'ENG-2023-118',
            'Electrical & Electronics Engineering',
            '+1 (555) 017-4482',
            sarah_pass,
            'student'
        ))
        sarah_id = cursor.lastrowid

        # Seed sample items
        sample_items = [
            (
                alex_id,
                'lost',
                'Space Grey MacBook Air M2 (13-inch)',
                'Electronics & Gadgets',
                'Left on 2nd-floor study cubicle #14 near the west windows. Has a GitHub Octocat sticker and a National Parks sticker on the cover.',
                'Main Library',
                '2026-11-15',
                None,
                'Lost',
                None,
                'alex.student@campus.edu / 555-014-9921'
            ),
            (
                sarah_id,
                'lost',
                'Brown Leather Fossil Bi-Fold Wallet',
                'Wallets & Purses',
                'Contains student transit card, university ID card for Sarah Mitchell, and emergency cash. Lost around lunchtime near the salad bar.',
                'Student Center / Cafeteria',
                '2026-11-16',
                None,
                'Lost',
                None,
                'sarah.mitchell@campus.edu'
            ),
            (
                sarah_id,
                'found',
                'Sony WH-1000XM5 Noise Cancelling Headphones (Silver)',
                'Electronics & Gadgets',
                'Found in lecture hall B-102 on desk row 3. Includes the original grey zipper carrying case and USB-C cable.',
                'Science Block B',
                '2026-11-14',
                None,
                'Claim Pending',
                'Handed over to Campus Security Desk (Room 105)',
                'security@campus.edu'
            ),
            (
                admin_id,
                'found',
                'Subaru Car Key with Red Braided Lanyard',
                'Keys & Access Cards',
                'Found near parking bay C-12 in the north lot after the university evening football game. Has a mini Swiss knife attached.',
                'Campus Parking Lot',
                '2026-11-16',
                None,
                'Found',
                'Stored at Main Security Office Safe Locker',
                '555-019-2834'
            ),
            (
                alex_id,
                'lost',
                'TI-84 Plus CE Graphing Calculator (Teal)',
                'Electronics & Gadgets',
                'Left in Lab Room 304 after Calculus seminar. Has small initials "AR" written on back battery door.',
                'Engineering Building',
                '2026-11-13',
                None,
                'Lost',
                None,
                'alex.student@campus.edu'
            ),
            (
                sarah_id,
                'found',
                'Matte Black HydroFlask Bottle (32oz)',
                'Water Bottles & Containers',
                'Found on the bench beside indoor basketball court 2. University hiking club sticker on front.',
                'Sports Complex & Gym',
                '2026-11-11',
                None,
                'Returned',
                'Reunited with owner (Michael T.)',
                'reception@gym.campus.edu'
            )
        ]

        cursor.executemany("""
            INSERT INTO items (
                user_id, item_type, title, category, description,
                location, event_date, image_path, status, custody_info, contact_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_items)

        # Seed a pending claim on the Sony headphones (item id 3) by Alex
        cursor.execute("""
            INSERT INTO claims (
                item_id, claimer_id, proof_description, proof_image, contact_phone, status, admin_remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            3,
            alex_id,
            'I left my Sony XM5 headphones in room B-102 on Thursday afternoon. The Bluetooth name is set to "Alex\'s XM5" and the inside right ear cup has a tiny scratch near the sensor.',
            None,
            '+1 (555) 014-9921',
            'Pending',
            'Awaiting verification at Campus Security Desk with student ID card.'
        ))

        # Seed activity log
        cursor.execute("""
            INSERT INTO activity_logs (user_id, action, details)
            VALUES (?, ?, ?)
        """, (admin_id, 'SYSTEM_INIT', 'System initialized with default campus data.'))

        conn.commit()

    conn.close()

def log_activity(user_id, action, details=""):
    """Records an event in the activity log."""
    try:
        execute_db(
            "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )
    except Exception:
        pass
