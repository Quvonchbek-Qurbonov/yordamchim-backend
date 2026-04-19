from sqlalchemy.orm import Session

from src.services import Service


def get_all_services(db_session: Session):
    services = db_session.query(Service).all()
    return services