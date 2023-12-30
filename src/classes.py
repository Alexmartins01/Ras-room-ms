from typing import List
import uuid
import datetime

from sqlalchemy import create_engine, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, DeclarativeBase, Session


DATABASE_URL = 'mysql+mysqldb://name:password@localhost:3306/RoomsDB'

# Create an engine
engine = create_engine(DATABASE_URL, echo=True)  # Set echo to True for debugging

# Create a base class for declarative class definitions
class Base(DeclarativeBase):
    ...

class Room(Base):
    __tablename__ = "room"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    floor: Mapped[int]
    capacity: Mapped[int]
    computers: Mapped[int]
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"))
    building: Mapped["Building"] = relationship(back_populates="rooms")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="room")

class Building(Base):
    __tablename__ = "building"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    rooms: Mapped[list[Room]] = relationship(back_populates="building")

class Schedule(Base):
    __tablename__ = "schedule_t"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    start: Mapped[datetime.datetime]
    end: Mapped[datetime.datetime]
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("room.id"))
    room: Mapped[Room] = relationship(back_populates="schedules")


# Demo of some features
Base.metadata.create_all(engine) # creates the tables on the database

session = Session(engine)

b1 = Building(id=uuid.uuid4(), name="asd")
r1 = Room(id=uuid.uuid4(), name="room name", floor=0, capacity=20, computers=10)
b1.rooms.append(r1) # this append synchronizes both related objects

session.add(r1) # this added both b1 and r1, due to their relation

session.flush() # add changes to transaction
session.commit() # commit transaction to the database

session.close()

class Scheduler:
    schedules: list[Schedule]

    def __init__(self) -> None:
        pass
    
    def schedule():
        ...
    
    def auto_schedule():
        ...
    
    def get_available_rooms():
        ...
    
    def get_schedule():
        ...
    
    def get_buildings():
        ...
    
    def get_building():
        ...