from flask import Blueprint, request, current_app, abort
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from rooms.classes import Building, Room, Schedule, AutoScheduleParams, ScheduleParams
import math
import datetime
import uuid
import itertools

bp = Blueprint("endpoints", __name__)

@bp.post("/schedule")
def schedule():
    r_data = request.get_data()
    params_l = ScheduleParams.list_from_json(r_data)
    with Session(current_app.engine) as session:
        scheduled_list: list[Schedule] = []
        for params in params_l:
            rooms = session.execute(select(Room.id).where(Room.id.in_(params.rooms))).scalars().all()
            if len(rooms)!=len(params.rooms):
                unknown_rooms = list(set(params.rooms)-set(rooms))
                return unknown_rooms, 404

            clashing_schedules = []
            for room_id in params.rooms:
                schedules = session.execute(
                    select(Schedule)
                        .where(
                            (Schedule.start<params.end_date_time) &
                            (Schedule.end>params.start_date_time) &
                            (Schedule.room_id==room_id)
                        )
                ).scalars().all()
                if len(schedules)>0:
                    clashing_schedules.extend(schedules)

                elif len(clashing_schedules)==0:
                    sch = Schedule(id=uuid.uuid4(),start=params.start_date_time, end=params.end_date_time, room_id=room_id)
                    scheduled_list.append(sch)
            
            if len(clashing_schedules)>0:
                return [s.id for s in clashing_schedules], 403

        session.add_all(scheduled_list)
        session.commit()
        return [s.id for s in scheduled_list], 200 
            


def try_auto_schedule(params: AutoScheduleParams, rooms: list[Room], session: Session, sch_mem: dict[uuid.UUID, Schedule]) -> list[Schedule] | None:
    beg_search = params.begin_datetime
    end_search = beg_search + datetime.timedelta(minutes=params.duration_minutes)
    schedules = []
    for room in rooms:
        if room.id in sch_mem:
            schedules.append(sch_mem[room.id])
        else:
            sch = session.execute(
                    select(Schedule)
                        .where(
                            (Schedule.start<params.end_datetime) &
                            (Schedule.end>params.begin_datetime) &
                            (Schedule.room_id==room.id))
                        .order_by(Schedule.start.asc())).scalars().all()
            sch_mem[room.id] = sch
            schedules.append(sch)
    
    inters_sch = []
    for sch in schedules:
        if len(sch)>0:
            inters_sch.append(sch)
    
    if len(inters_sch)>0:
        for sch in inters_sch[0]:
            if sch.start < end_search and sch.end > beg_search:
                beg_search = sch.end
                end_search = beg_search + datetime.timedelta(minutes=params.duration_minutes)
                if end_search > params.end_datetime:
                    return None

            intersected = False
            for other_room_i in range(1,len(schedules)):
                if intersected:
                    break
                for other_sch in schedules[other_room_i]:
                    if other_sch.start < end_search and other_sch.end > beg_search:
                        beg_search = other_sch.end
                        end_search = beg_search + datetime.timedelta(minutes=params.duration_minutes)
                        intersected = True
                        if end_search > params.end_datetime:
                            return None
                        break
    
    valid_schs = []
    for room in rooms:
        valid_schs.append(Schedule(id=uuid.uuid4(), start=beg_search, end=end_search, room_id=room.id))
    
    return valid_schs

# reserves some rooms to fill totalcap for duration minutes,
# between begin and end, on selected buildings
@bp.post("/auto-schedule")
def auto_schedule():
    with Session(current_app.engine) as session:
        r_data = request.get_data()
        params = AutoScheduleParams.from_json(r_data)
        if params.end_datetime < params.begin_datetime + datetime.timedelta(minutes=params.duration_minutes):
            abort(403)
        rooms = None
        if len(params.buildings)>0:
            rooms = session.execute(
                select(Room)
                    .where(Room.building_id.in_(params.buildings))
                    .order_by(Room.capacity.desc())).scalars().all()
        else:
            rooms = session.execute(select(Room).order_by(Room.capacity.desc())).scalars().all()

        if len(rooms)==0:
            abort(403)

        search_rooms = []
        for room in rooms:
            if room.capacity < params.total_capacity:
                break
            search_rooms.append(room)

        sch_mem = {}
        if len(search_rooms)>0:
            for room in reversed(search_rooms):
                schs = try_auto_schedule(params, [room], session, sch_mem)
                if schs is not None:
                    session.add_all(schs)
                    session.commit()
                    return [s.id for s in schs], 200

        for i in range(2,len(rooms)):
            room_cmbs = itertools.combinations(rooms, i)
            for room_cmb in room_cmbs:
                t_cap = 0
                for room in room_cmb:
                    t_cap += room.capacity
                if t_cap < params.total_capacity:
                    break
                schs = try_auto_schedule(params, room_cmb, session, sch_mem)
                if schs is not None:
                    session.add_all(schs)
                    session.commit()
                    return [s.id for s in schs], 200
                    
        abort(403)
            

@bp.get("/buildings")
def buildings():
    with Session(current_app.engine) as session:
        st = select(Building)
        buildings = session.execute(st).scalars()
        ret_buildings = []
        for building in buildings:
            rooms = []
            for room in building.rooms:
                rd = room.to_dict()
                del rd["building_id"]
                rooms.append(rd)

            d = building.to_dict()
            d["rooms"] = rooms
            ret_buildings.append(d)

        return ret_buildings
            