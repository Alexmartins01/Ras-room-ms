import uuid
import datetime

from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace 'mysql+mysqlconnector' with 'mysql+pymysql' if you are using pymysql
DATABASE_URL = 'mysql+mysqlconnector://username:password@localhost:3306/your_database'

# Create an engine
engine = create_engine(DATABASE_URL, echo=True)  # Set echo to True for debugging

# Create a base class for declarative class definitions
Base = declarative_base()

class Room:
    id: uuid.UUID
    name: str
    capacity: int
    computers: int

class Building:
    id: uuid.UUID
    name: str
    rooms: list[Room]

class Schedule:
    id: uuid.UUID
    start: datetime.datetime
    end: datetime.datetime
    room: Room

    def __init__(self) -> None:
        pass

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