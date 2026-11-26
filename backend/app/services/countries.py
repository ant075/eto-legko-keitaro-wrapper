from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Country


def list_countries(db: Session) -> list[Country]:
    return list(db.scalars(select(Country).order_by(Country.name_ru)))

