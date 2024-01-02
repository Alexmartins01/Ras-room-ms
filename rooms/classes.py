import uuid
import datetime
import json

from typing import Any, List
from sqlalchemy import create_engine, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, DeclarativeBase, Session, sessionmaker
from dataclasses import dataclass


# Create a base class for declarative class definitions
class Base(DeclarativeBase):
    ...

class Room(Base):
    __tablename__ = "room"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    floor: Mapped[int]
    capacity: Mapped[int]
    computers: Mapped[int]
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"))
    building: Mapped["Building"] = relationship(back_populates="rooms")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="room")

    def __repr__(self) -> str:
        return f"name:{self.name}, floor:{self.floor}, cap:{self.capacity}, pcs:{self.computers}"

    def to_dict(self) -> dict:
        return {
            "id" : self.id,
            "name" : self.name,
            "floor" : self.floor,
            "capacity" : self.capacity,
            "computers" : self.computers,
            "building_id" : self.building_id
        }

class Building(Base):
    __tablename__ = "building"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    rooms: Mapped[list[Room]] = relationship(back_populates="building", cascade='all, delete')

    def to_dict(self) -> dict:
        return {
            "id" : self.id,
            "name" : self.name,
        }

class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    start: Mapped[datetime.datetime]
    end: Mapped[datetime.datetime]
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("room.id"))
    room: Mapped[Room] = relationship(back_populates="schedules")

    def to_dict(self) -> dict:
        return {
            "id" : self.id,
            "start" : self.start,
            "end": self.end,
            "room_id" : self.room_id
        }


@dataclass
class AutoScheduleParams:
    begin_datetime: datetime.datetime
    end_datetime: datetime.datetime
    duration_minutes: int
    total_capacity: int
    buildings: list[uuid.UUID]

    @staticmethod
    def from_json(json_s:str) -> 'AutoScheduleParams':
        d = json.loads(json_s)
        begin_datetime = datetime.datetime.fromisoformat(d['begin_datetime'])
        end_datetime = datetime.datetime.fromisoformat(d['end_datetime'])
        duration_minutes = int(d['duration_minutes'])
        total_capacity = int(d['total_capacity'])
        buildings = []
        for id in d['buildings']:
            buildings.append(uuid.UUID(id))
        
        return AutoScheduleParams(begin_datetime, end_datetime, duration_minutes, total_capacity, buildings)

@dataclass
class ScheduleParams:
    start_date_time: datetime.datetime
    end_date_time: datetime.datetime
    rooms: list[uuid.UUID]

    @staticmethod
    def from_json(json_s:str) -> 'ScheduleParams':
        d = json.loads(json_s)
        p = ScheduleParams()
        p.start_date_time = datetime.datetime.fromisoformat(d['start_date_time'])
        p.end_date_time = datetime.datetime.fromisoformat(d['end_date_time'])
        p.rooms = []
        for id in d['rooms']:
            p.rooms.append(uuid.UUID(id))
        return p

    @staticmethod
    def list_from_json(json_s:str) -> List['ScheduleParams']:
        l = json.loads(json_s)
        sch_l = []
        for params in l:
            start_date_time = datetime.datetime.fromisoformat(params['start_date_time'])
            end_date_time = datetime.datetime.fromisoformat(params['end_date_time'])
            rooms = []
            for id in params['rooms']:
                rooms.append(uuid.UUID(id))
            p = ScheduleParams(start_date_time, end_date_time, rooms)
            sch_l.append(p)

        return sch_l



class RoomManager:
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
    
    def add_rooms():
        ...
    
    def delete_room():
        ...