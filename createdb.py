"""This module creates a database for the application."""
import sqlite3
import os

# If the roleping.db file doesn't exist, create it using the schema in roleping.sql
if not os.path.isfile('roleping.db'):
    conn = sqlite3.connect('roleping.db')
    c = conn.cursor()
    with open('roleping.sql') as f:
        c.executescript(f.read())
    conn.commit()
    conn.close()