import sqlite3
from datetime import datetime

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

# Insert dummy users
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
               ("Chinthiya", "chin@example.com"))

cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
               ("Anu", "anu@example.com"))

# Insert dummy books
cursor.execute("INSERT INTO books (title, author, available_copies) VALUES (?, ?, ?)",
               ("Harry Potter", "J.K. Rowling", 3))

cursor.execute("INSERT INTO books (title, author, available_copies) VALUES (?, ?, ?)",
               ("Atomic Habits", "James Clear", 2))

conn.commit()
conn.close()

print("Dummy data inserted successfully!")