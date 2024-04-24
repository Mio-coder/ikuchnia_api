from datetime import time, date, datetime
from pprint import pprint
from typing import Optional

from msgspec import Struct
from requests import Session


class ProjOrdered(Struct):
    do_kiedy_zamowic_dzis: time
    do_kiedy_zamowic: time
    sposob_zamawiania: str
    pokaz_dania: bool
    ID: int
    guzik_edytuj: str
    rezygnacja: time


class RawProjOrdered(Struct):
    do_kiedy_zamowic_dzis: time
    do_kiedy_zamowic: time
    sposob_zamawiania: str
    pokaz_dania: str
    ID: str
    guzik_edytuj: str
    rezygnacja: time


class RawMealsOrdered(Struct):
    html: str
    date: str
    day: int
    sql: str
    proj: list[RawProjOrdered]
    blokada_zamawiania: bool


class MealOrdered(Struct):
    type: str
    name: str


class MealsOrdered(Struct):
    meals: list[MealOrdered]
    can_edit: bool
    is_canceled: bool
    day_name: str
    order_date: date
    order_lock: bool
    proj: list[ProjOrdered]
    "don't know what it is"
    raw: Optional[RawMealsOrdered] = None


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
    date: date
    day_name: str
    soup: MealAvailable
    meat_dish: MealAvailable
    vegetarian_dish: MealAvailable
    bonus_dish: MealAvailable
    juice: MealAvailable
    price_before: float
    price_after: float
    raw: Optional[RawMealsAvailable] = None

    @property
    def dishes(self):
        return {
            "soup": self.soup,
            "meat_dish": self.meat_dish,
            "vegetarian_dish": self.vegetarian_dish,
            "bonus_dish": self.bonus_dish,
            "juice": self.juice,
        }


class Sid(Struct):
    timestamp: datetime
    sid: str

    def set(self, session: Session):
        session.cookies.set("PHPSESSID", self.sid)


