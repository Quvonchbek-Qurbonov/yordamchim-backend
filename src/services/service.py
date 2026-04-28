from sqlalchemy.orm import Session

from src.services import Service


def get_all_services(db_session: Session, skip: int = 0, limit: int = 100):
    services = db_session.query(Service).offset(skip).limit(limit).all()
    return services