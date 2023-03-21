"""This module creates a database for the application."""
import sqlite3
import os

# If the database.db file doesn't exist, create it using the schema in roleping.sql
if not os.path.isfile('database.db'):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    with open('roleping.sql') as f:
        c.executescript(f.read())
    conn.commit()
    conn.close()