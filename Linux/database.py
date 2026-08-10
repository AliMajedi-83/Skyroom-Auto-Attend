import sqlite3
import json

DB_NAME = "classes.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            password TEXT,
            class_name TEXT,
            link TEXT,
            schedule TEXT,
            rec_video INTEGER,
            rec_audio INTEGER,
            save_path TEXT,
            silence_timeout INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_class(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO classes (user_name, password, class_name, link, schedule, rec_video, rec_audio, save_path, silence_timeout)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def update_class(class_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE classes 
        SET user_name=?, password=?, class_name=?, link=?, schedule=?, rec_video=?, rec_audio=?, save_path=?, silence_timeout=?
        WHERE id=?
    ''', data + (class_id,))
    conn.commit()
    conn.close()

def get_classes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classes")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_class(class_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE id=?", (class_id,))
    conn.commit()
    conn.close()
