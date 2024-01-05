from flask import Blueprint, request, current_app, abort
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import Session
from rooms.classes import Building, Room, Schedule, AutoScheduleParams, ScheduleParams
from types import SimpleNamespace
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
        valid_schs.append(Schedule(id=uuid.uuid4(), start=beg_search, end=end_search, room=room))
    
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
                    data = [s.to_dict_full() for s in schs]
                    session.commit()
                    return data, 200

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
                    data = [s.to_dict_full() for s in schs]
                    session.commit()
                    return data, 200
                    
        abort(403)
            
@bp.post("/update")
def update():
    r_data = [SimpleNamespace(**x) for x in request.get_json()]
    building_names = set()
    room_names = set()
    for data in r_data:
        room_names.add(data.room_values['name'])
        building_names.add(data.building_name)
    
    with Session(current_app.engine) as session:
        db_buildings = session.scalars(
            select(Building)
                .where(Building.name.in_(building_names))
        ).all()
        
        db_rooms = session.scalars(
            select(Room)
                .where(Room.name.in_(room_names))
        ).all()

        if len(db_rooms)>0:
            abort(403)

        buildings: dict[str, Building] = {}
        b_name_id : dict[str, uuid.UUID] = {}
        for b in db_buildings:
            buildings[b.name] = b
            b_name_id[b.name] = b.id
        
        #rooms: dict[str, Room] = {}
        #for r in db_rooms:
        #    rooms[r.name] = r
        
        for data in r_data:
            if data.building_name not in buildings:
                buildings[data.building_name] = Building(id=uuid.uuid4(), name=data.building_name)

            r = Room(
                id=uuid.uuid4(), 
                name=data.room_values['name'], 
                floor=data.room_values['floor'], 
                capacity=data.room_values['capacity'],
                computers=data.room_values['computers'],
                building=buildings[data.building_name]
            )
            session.add(r)
            #else:
                #session.execute(delete(Schedule).where(Schedule.room_id==r.id))
                #        
                #r.capacity = data.room_values['capacity']
                #r.computers = data.room_values['computers']
                #r.floor = data.room_values['floor']
                #r.building = buildings[data.building_name]
                #session.add(r)
        
        session.commit()
                
    return '', 204

@bp.get('/schedule/<schedule_id>')
def get_schedule(schedule_id):
    sch_uuid = uuid.UUID(schedule_id)
    with Session(current_app.engine) as session:
        sch = session.get(Schedule, sch_uuid)
        if sch is None:
            abort(404)
        data = sch.to_dict_full()
        return data, 200

        
@bp.post("/unschedule")
def unschedule():
    sch_ids = set(uuid.UUID(x) for x in request.get_json())

    with Session(current_app.engine) as session:
        db_sch_ids = set(session.scalars(
            select(Schedule.id)
                .where(Schedule.id.in_(sch_ids))
        ))

        dif_ids = sch_ids - db_sch_ids
        if len(dif_ids)>0:
            return dif_ids, 404

        session.execute(delete(Schedule).where(Schedule.id.in_(sch_ids)))
        session.commit()
    
    return '', 204

@bp.get('/room/<room_id>')
def get_room(room_id):
    r_uuid = uuid.UUID(room_id)
    with Session(current_app.engine) as session:
        r = session.get(Room, r_uuid)
        if r is None:
            abort(404)

        rd = r.to_dict()
        del rd['building_id']
        d = {
            'room': rd,
            'building_id': r.building_id,
            'building_name': r.building.name
        }
        return d, 200 


@bp.delete("/room/<room_id>")
def delete_room(room_id):
    r_uuid = uuid.UUID(room_id)
    with Session(current_app.engine) as session:
        r = session.get(Room, r_uuid)
        if r is None:
            abort(404)
        
        session.delete(r)
        session.commit()

    return '', 204

@bp.get("/building/<building_id>")
def get_building(building_id):
    b_uuid = uuid.UUID(building_id)
    with Session(current_app.engine) as session:
        b = session.get(Building, b_uuid)
        if b is None:
            abort(404)
        d = b.to_dict_with_rooms()
        return d, 200

@bp.get("/buildings")
def get_buildings():
    with Session(current_app.engine) as session:
        st = select(Building)
        buildings = session.execute(st).scalars()
        ret_buildings = []
        for building in buildings:
            ret_buildings.append(building.to_dict_with_rooms())

        return ret_buildings
            