from datetime import time
from pprint import pprint
from msgspec import Struct


class Proj(Struct):
    do_kiedy_zamowic_dzis: time
    do_kiedy_zamowic: time
    sposob_zamawiania: str
    pokaz_dania: str
    ID: str
    guzik_edytuj: str
    rezygnacja: time


class DayMeal(Struct):
    html: str
    date: str
    day: int
    sql: str
    proj: list[Proj]
    blokada_zamawiania: bool


if __name__ == '__main__':
    from msgspec.json import decode

    with open("example.json") as f:
        obj = decode(f.read(), type=DayMeal)
    pprint(obj)
