import sqlite3
import os

def update_db(db_file, schema_file):
    # Check if the database file exists
    if os.path.isfile(db_file):
        return

    # If not, create the database file
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Read the schema file and execute it
    with open(schema_file, 'r') as f:
        schema = f.read()
    c.executescript(schema)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Database created")