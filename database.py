import sqlite3
import os
import json
import logging
from pathlib import Path

DB_DIR = os.path.join(str(Path.home()), ".config", "fstasearch")
DB_FILE = os.path.join(DB_DIR, "fstasearch.db")

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Ensure config dir exists
            if not os.path.exists(DB_DIR):
                os.makedirs(DB_DIR)
            self.db_path = DB_FILE
        else:
            self.db_path = db_path
            
        self.connect()
        self.init_db()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        cursor = self.conn.cursor()
        
        # Settings Table (key, value)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Index Table (path, type) - type: 'file' or 'dir'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY,
                type TEXT
            )
        ''')
        
        self.conn.commit()

    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        json_val = json.dumps(value)
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, json_val))
        self.conn.commit()

    def get_index(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT path, type FROM file_index')
        rows = cursor.fetchall()
        
        files = []
        dirs = []
        for path, dtype in rows:
            if dtype == 'file':
                files.append(path)
            else:
                dirs.append(path)
        return files, dirs

    def update_index(self, files, dirs):
        cursor = self.conn.cursor()
        # Full replace strategy for simplicity? Or differential?
        # Full replace is safer for consistency.
        cursor.execute('DELETE FROM file_index')
        
        data = [(f, 'file') for f in files] + [(d, 'dir') for d in dirs]
        # Batch insert
        cursor.executemany('INSERT OR IGNORE INTO file_index (path, type) VALUES (?, ?)', data)
        self.conn.commit()

    def close(self):
        self.conn.close()

# Global instance
db = DatabaseManager()
