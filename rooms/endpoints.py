from flask import Blueprint, request, current_app
from sqlalchemy import select
from sqlalchemy.orm import Session
from rooms.classes import Building, Room


bp = Blueprint("endpoints", __name__)

@bp.route("/")
def yo():
    return "<p>Hello, World!</p>"

@bp.route("/yep/<var>")
def yep(var):
    return f"<p>{var}</p>"

@bp.route("/buildings")
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
            