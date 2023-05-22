"""Script for one-time database actions."""

import os
import sys
import sqlite3
import sqlalchemy

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Server, ServerSettings, NameReply, Rank

# Old database file "database.db"
old_db = sqlite3.connect('database.db')
# New database file "alchemy.db"
new_db = create_engine('sqlite:///alchemy.db', echo=True)

# Create all tables in the new database.
Base.metadata.create_all(new_db)

def import_setting(setting: str, value: str, server_id: int):
    """Import a setting from the old database to the new database."""
    with Session(new_db) as conn:
        objects = []
        # Check if the server exists in the new database.
        server = conn.query(Server).filter(Server.id == server_id).first()
        if server is None:
            new_server = Server(id=server_id)
            objects.append(new_server)
        # Insert the setting into the new database.
        new_setting = ServerSettings(server_id=server_id, setting=setting, value=value)
        objects.append(new_setting)
        conn.add_all(objects)
        conn.commit()


# Import all settings from the old database to the new database.
# Roleping
# Row format of the old Roleping table: (server_id, timer_duration, rpenabled, rprole)
print('Importing roleping settings...')
for row in old_db.execute('SELECT * FROM roleping'):
    import_setting('rp_timer_duration', str(row[1]), row[0])
    import_setting('rp_enabled', str(row[2]), row[0])
    import_setting('rp_role', str(row[3]), row[0])

# Suggest
# Row format of the old Suggest table: (server_id, enabled, suggestchannel, eventchannel)
print('Importing suggest settings...')
for row in old_db.execute('SELECT * FROM suggest'):
    import_setting('sg_enabled', str(row[1]), row[0])
    import_setting('sg_channel', str(row[2]), row[0])
    import_setting('sg_event_channel', str(row[3]), row[0])

# Welcome
# Row format of the old Welcome table: (server_id, enabled, welcomechannel)
print('Importing welcome settings...')
for row in old_db.execute('SELECT * FROM welcome'):
    import_setting('wc_enabled', str(row[1]), row[0])
    import_setting('wc_channel', str(row[2]), row[0])

# Userranks
# Row format of the old Userranks table: (server_id, role_id, rank integer)
# This does not get imported to the settings table, but instead it's own Rank table.
print('Importing userranks...')
for row in old_db.execute('SELECT * FROM ranks'):
    with Session(new_db) as conn:
        objects = []
        # Check if the server exists in the new database.
        server = conn.query(Server).filter(Server.id == row[0]).first()
        if server is None:
            new_server = Server(id=row[0])
            objects.append(new_server)
        # Insert the setting into the new database.
        new_rank = Rank(server_id=row[0], role_id=row[1], rank=row[2])
        objects.append(new_rank)
        conn.add_all(objects)
        conn.commit()

# NameReply is not getting imported, because it did not log server_id.
print('namereply is not getting imported, because it did not log server_id.')

# Close the old database.
old_db.close()

print('Done.')
