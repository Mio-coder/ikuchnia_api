from datetime import time
from pprint import pprint
from typing import Optional

from msgspec import Struct


class Proj(Struct):
    do_kiedy_zamowic_dzis: time
    do_kiedy_zamowic: time
    sposob_zamawiania: str
    pokaz_dania: bool
    ID: int
    guzik_edytuj: str
    rezygnacja: time


class RawProj(Struct):
    do_kiedy_zamowic_dzis: time
    do_kiedy_zamowic: time
    sposob_zamawiania: str
    pokaz_dania: str
    ID: str
    guzik_edytuj: str
    rezygnacja: time

    def optimize(self):
        return Proj(
            self.do_kiedy_zamowic_dzis,
            self.do_kiedy_zamowic,
            self.sposob_zamawiania,
            self.pokaz_dania == "yes",
            int(self.ID),
            self.guzik_edytuj,
            self.rezygnacja
        )


class RawMeals(Struct):
    html: str
    date: str
    day: int
    sql: str
    proj: list[RawProj]
    blokada_zamawiania: bool


class RawMealsAvailable(Struct):
    html: str
    cena_przed: str
    cena_po: str


class MealAvailable(Struct):
    title: str
    meal_id_label: int
    meal_id: int
    pricing_group: int
    selected: bool
    item: str


class MealsAvailable(Struct):
    day_no: int
    day_name: str
    meals: dict[str, MealAvailable]
    price_before: float
    price_after: float
    raw: Optional[RawMeals] = None


if __name__ == '__main__':
    from msgspec.json import decode

    with open("example.json") as f:
        obj = decode(f.read(), type=RawMeals)
    pprint(obj)
