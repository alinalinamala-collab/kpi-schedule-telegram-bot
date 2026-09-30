import sqlite3

DB_NAME = "bot_database.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Таблиця користувачів
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            group_id INTEGER
        )
        """)
        
        # Таблиця Zoom-посилань
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zoom_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            subject_name TEXT,
            link TEXT,
            UNIQUE(group_id, subject_name)
        )
        """)
        conn.commit()

def set_user_group(user_id: int, group_id: int):
    """Збереження або оновлення групи для користувача"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (user_id, group_id) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET group_id=excluded.group_id
        """, (user_id, group_id))
        conn.commit()

def get_user_group(user_id: int) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def add_zoom_link(group_id: int, subject_name: str, link: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO zoom_links (group_id, subject_name, link) VALUES (?, ?, ?)
        ON CONFLICT(group_id, subject_name) DO UPDATE SET link=excluded.link
        """, (group_id, subject_name, link))
        conn.commit()

def get_zoom_link(group_id: int, subject_name: str) -> str:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT link FROM zoom_links WHERE group_id = ? AND subject_name = ?", 
            (group_id, subject_name)
        )
        result = cursor.fetchone()
        return result[0] if result else "Посилання відсутнє"