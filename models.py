"""SQLAlchemy models for discord bot."""

from typing import Any
import sqlalchemy
from sqlalchemy import ForeignKey, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, relationship

class Base(DeclarativeBase):
    """Base class for all models."""
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class Server(Base):
    __tablename__ = 'servers'

    # This is the server's ID on Discord. Guaranteed to be unique.
    id = Column(Integer, primary_key=True, unique=True)

    def __repr__(self):
        return f"<Server(id={self.id}, name={self.name})>"
    
    def __str__(self):
        return self.name
    
# Property bag for all bot-related settings for a server.
class ServerSettings(Base):
    __tablename__ = 'server_settings'

    # ID of the settings object. This is not the same as the server's ID.
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)
    # ID of the server this settings object belongs to.
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    # String representing the setting name.
    setting = Column(String, nullable=False)
    # String representing the setting value.
    value = Column(String, nullable=False)

    def __repr__(self):
        return f"<ServerSettings(id={self.id}, server_id={self.server_id}, setting={self.setting}, value={self.value})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.setting}: {self.value}"
    
# Name-reply table, for responses to specific user names
class NameReply(Base):
    __tablename__ = 'name_reply'

    # ID of the name-reply object. This is not the same as the user's ID.
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)
    # ID of the server this name-reply object belongs to.
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    # ID of the user this name-reply object belongs to.
    user_id = Column(Integer, nullable=False)
    # URL of the image to reply with.
    image_url = Column(String, nullable=False)

    def __repr__(self):
        return f"<NameReply(id={self.id}, server_id={self.server_id}, user_id={self.user_id}, image_url={self.image_url})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.user_id}: {self.image_url}"
    
# User ranks for a server.
class Rank(Base):
    __tablename__ = 'ranks'

    # ID of the rank object. This is not the same as the server's ID.
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)
    # ID of the server this rank object belongs to.
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    # ID of the role this rank object belongs to.
    role_id = Column(Integer, nullable=False)
    # Integer representing the rank value.
    rank = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Rank(id={self.id}, server_id={self.server_id}, role_id={self.role_id}, rank={self.rank})>"
    
    def __str__(self):
        return f"{self.server_id}; {self.role_id}: {self.rank}"