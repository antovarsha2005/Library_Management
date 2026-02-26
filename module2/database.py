import sqlite3
from contextlib import contextmanager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    address TEXT,
                    membership_type TEXT DEFAULT 'Standard',
                    status TEXT DEFAULT 'Active',
                    joined_date TEXT,
                    last_active TEXT,
                    books_issued INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create books table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    isbn TEXT UNIQUE,
                    category TEXT,
                    quantity INTEGER DEFAULT 1,
                    available INTEGER DEFAULT 1,
                    published_year INTEGER,
                    added_date TEXT
                )
            ''')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    book_id INTEGER,
                    issue_date TEXT,
                    due_date TEXT,
                    return_date TEXT,
                    status TEXT DEFAULT 'Issued',
                    fine_amount REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def get_total_users(self):
        """Get total number of users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
    
    def get_active_users(self):
        """Get number of active users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'Active'")
            return cursor.fetchone()[0]
    
    def get_total_books(self):
        """Get total number of books"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(quantity) FROM books")
            return cursor.fetchone()[0] or 0
    
    def get_books_issued(self):
        """Get number of books currently issued"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Issued'")
            return cursor.fetchone()[0]
    
    def get_recent_activities(self, limit=10):
        """Get recent activities"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 'User Added' as action, name, joined_date as date 
                FROM users ORDER BY joined_date DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    
    def get_all_users_paginated(self, page=1, per_page=10):
        """Get paginated list of users"""
        offset = (page - 1) * per_page
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            return cursor.fetchall()
    
    def get_all_users(self):
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return cursor.fetchall()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone()
    
    def add_user(self, user_data):
        """Add new user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, email, phone, address, membership_type, joined_date, status)
                VALUES (:name, :email, :phone, :address, :membership_type, :joined_date, 'Active')
            ''', user_data)
            conn.commit()
            return cursor.lastrowid
    
    def update_user(self, user_id, user_data):
        """Update user information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET name = :name, email = :email, phone = :phone, 
                    address = :address, membership_type = :membership_type, status = :status
                WHERE id = ?
            ''', {**user_data, 'id': user_id})
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_user(self, user_id):
        """Delete user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_users(self, query):
        """Search users by name, email, or phone"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
                ORDER BY name
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            return cursor.fetchall()