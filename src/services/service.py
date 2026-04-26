from typing import List

from sqlalchemy.orm import Session

from src.services import Service


def get_all_services(db_session: Session, skip: int, limit: int):
    services = db_session.query(Service).offset(skip).limit(limit).all()
    return services