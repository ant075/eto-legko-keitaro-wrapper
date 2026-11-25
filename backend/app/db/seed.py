import pycountry
from babel import Locale

from app.db.session import SessionLocal
from app.models import Country


def seed_countries() -> None:
    russian = Locale("ru")
    with SessionLocal.begin() as session:
        for item in pycountry.countries:
            name_ru = russian.territories.get(item.alpha_2, item.name)
            session.merge(Country(code=item.alpha_2, name_ru=name_ru))


if __name__ == "__main__":
    seed_countries()

