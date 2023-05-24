"""SQLAlchemy models for discord bot."""

from typing import Any
import sqlalchemy
import logging
from sqlalchemy import ForeignKey, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, relationship, Session

class Base(DeclarativeBase):
    """Base class for all models."""
    __abstract__ = True
    id = MappedColumn(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)

class Server(Base):
    __tablename__ = 'servers'

    # This is the server's ID on Discord. Guaranteed to be unique.
    server_id = MappedColumn(Integer, unique=True, nullable=False)

    def __repr__(self):
        return f"<Server(id={self.id}, name={self.name})>"
    
    def __str__(self):
        return self.name
    
# Property bag for all bot-related settings for a server.
class ServerSettings(Base):
    __tablename__ = 'server_settings'

    # ID of the server this settings object belongs to.
    server_id = MappedColumn(Integer, ForeignKey('servers.server_id'), nullable=False)
    # String representing the setting name.
    setting = MappedColumn(String, nullable=False)
    # String representing the setting value.
    value = MappedColumn(String, nullable=False)

    def __repr__(self):
        return f"<ServerSettings(id={self.id}, server_id={self.server_id}, setting={self.setting}, value={self.value})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.setting}: {self.value}"
    
# Name-reply table, for responses to specific user names
class NameReply(Base):
    __tablename__ = 'name_reply'

    # ID of the server this name-reply object belongs to.
    server_id = MappedColumn(Integer, ForeignKey('servers.server_id'), nullable=False)
    # ID of the user this name-reply object belongs to.
    user_name = MappedColumn(Integer, nullable=False)
    # URL of the image to reply with.
    image_url = MappedColumn(String, nullable=False)

    def __repr__(self):
        return f"<NameReply(id={self.id}, server_id={self.server_id}, user_id={self.user_id}, image_url={self.image_url})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.user_id}: {self.image_url}"
    
# User ranks for a server.
class Rank(Base):
    __tablename__ = 'ranks'

    # ID of the server this rank object belongs to.
    server_id = MappedColumn(Integer, ForeignKey('servers.server_id'), nullable=False)
    # ID of the role this rank object belongs to.
    role_id = MappedColumn(Integer, nullable=False)
    # Integer representing the rank value.
    rank = MappedColumn(Integer, nullable=False)

    def __repr__(self):
        return f"<Rank(id={self.id}, server_id={self.server_id}, role_id={self.role_id}, rank={self.rank})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.role_id}: {self.rank}"
    
# helper function for getting a server settings value
def get_setting(session: Session, server_id: int, setting: str) -> str:
    """Gets the value of a server setting."""
    try:
        result = session.query(ServerSettings).filter(ServerSettings.server_id == server_id, ServerSettings.setting == setting).first().value
    except AttributeError:
        result = None
    return result

# helper function for setting a server settings value
def set_setting(session: Session, server_id: int, setting: str, value: str) -> None:
    """Sets the value of a server setting."""
    try:
        session.query(ServerSettings).filter(ServerSettings.server_id == server_id, ServerSettings.setting == setting).first().value = value
        # session.commit()
        # Commented out because this is handled by the caller
    except AttributeError:
        logging.getLogger('discord').warning(f"Attempted to set setting {setting} for server {server_id}, but it doesn't exist. Creating it now.")
        session.add(ServerSettings(server_id=server_id, setting=setting, value=value))
        # session.commit()
        # Commented out because this is handled by the caller
        return None
    

# Helper function to check if a setting for the server exists in the database
# If not, use the provided default value and insert it into the database
def check_setting(server_id: int, c: Session, setting: str, default: str) -> bool:
    """Check if a setting for the server exists in the database.
    If not, use the provided default value and insert it into the database.
    Returns True if the setting exists or it was successfully inserted into the database, False otherwise."""
    try:
        if get_setting(c, server_id, setting) is None:
            set_setting(c, server_id, setting, default)
        return True
    except sqlalchemy.exc.SQLAlchemyError:
        return False