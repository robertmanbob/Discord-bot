"""This module creates a database for the application."""
import sqlite3
import os

# Open the database and run the query in the specified file
conn = sqlite3.connect('database.db')
c = conn.cursor()
with open('suggest.sql', 'r') as f:
    c.executescript(f.read())
conn.commit()
conn.close()
print('updated database')