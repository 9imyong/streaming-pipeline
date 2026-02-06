from sqlalchemy import Column, TEXT, INT, BIGINT, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    user_id = Column(BIGINT, nullable=False, autoincrement=True, primary_key=True)
    bibun = Column(TEXT, nullable=False)
    junbun = Column(TEXT, nullable=False)
    groupCode = Column(INT, ForeignKey("group.group_id"), nullable=False)
    
    group = relationship("Group", backref="users")

class Group(Base):
    __tablename__ = "group"

    group_id = Column(Integer, nullable=False, primary_key=True)
    # Add other columns of the group table
