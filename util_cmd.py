from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from urllib import request

from rooms.classes import Base, Room, Building, Schedule
import os, sys, uuid, json

if len(sys.argv)!=2:
    exit(0)

load_dotenv()

db_host = os.getenv("DB_HOST", "localhost")
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "")
db_name = os.getenv("DB_NAME", "default")

DATABASE_URL = f'mysql+mysqldb://{db_user}:{db_password}@{db_host}:3306/{db_name}'

# Create an engine
engine = create_engine(DATABASE_URL, echo=True)

match sys.argv[1]:
    case 'create':
        Base.metadata.create_all(engine)
    case 'drop':
        Base.metadata.drop_all(engine)
    case 'seed':
        with Session(engine) as session:
            b1 = Building(id=uuid.uuid4(), name="asd")
            for i in range(0, 5):
                r1 = Room(id=uuid.uuid4(), name=f"asd_room{i}", floor=0, capacity=20+(i*5), computers=10+(i*5))
                b1.rooms.append(r1)
            b2 = Building(id=uuid.uuid4(), name="bsd")
            for i in range(0, 5):
                r1 = Room(id=uuid.uuid4(), name=f"bsd_room{i}", floor=0, capacity=20+(i*5), computers=10+(i*5))
                b2.rooms.append(r1)
            session.add(b1)
            session.add(b2)
            session.commit()
    case 'schedule':
        room_uuids = []
        with Session(engine) as session:
            rooms = session.execute(select(Room)).scalars().all()
            room_uuids.append(rooms[0].id)
            room_uuids.append(rooms[1].id)

        req_data = [
            {
                'start_date_time': '2024-01-01T20:00:00',
                'end_date_time': '2024-01-01T21:00:00',
                #'rooms' : [uuid.uuid4().hex]
                'rooms' : [u.hex for u in room_uuids]
            }
        ]
        req_data_j = json.dumps(req_data).encode()
        req = request.Request("http://127.0.0.1:8000/schedule")
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(req_data_j))
        response = request.urlopen(req, req_data_j)
        print(json.loads(response.read().decode('utf-8')))
    case 'auto-schedule':
        room_uuids = []
        with Session(engine) as session:
            rooms = session.execute(select(Room)).scalars().all()
            room_uuids.append(rooms[0].id)
            room_uuids.append(rooms[1].id)

        req_data = {
                'begin_datetime': '2024-01-01T20:00:00',
                'end_datetime': '2024-01-01T21:00:00',
                'duration_minutes':45,
                'total_capacity':200,
                'buildings':[],
            }

        req_data_j = json.dumps(req_data).encode()
        req = request.Request("http://127.0.0.1:8000/auto-schedule")
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(req_data_j))
        response = request.urlopen(req, req_data_j)
        print(json.dumps(json.loads(response.read().decode('utf-8')), indent=4))
    
    case 'update':
        b_names = ['asd','bsd']
        req_data = []
        for bn in b_names:
            for i in range(0,5):
                req_data.append(
                    {
                        'room_values': {
                            'name': f'{bn}_room{i}',
                            'capacity': 20+5*i,
                            'computers': 20+5*i,
                            'floor': i,
                        },
                        'building_name': bn,
                    }
                )

        req_data_j = json.dumps(req_data).encode()
        
        req = request.Request("http://127.0.0.1:8000/update")
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(req_data_j))
        response = request.urlopen(req, req_data_j)
        print(response.status)

    case 'unschedule':
        req_data = []
        with Session(engine) as session:
            schs = session.scalars(select(Schedule))
            for sch in schs:
                req_data.append(sch.id.hex)

        req_data_j = json.dumps(req_data).encode()
        
        req = request.Request("http://127.0.0.1:8000/unschedule")
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(req_data_j))
        response = request.urlopen(req, req_data_j)
        print(response.status)
