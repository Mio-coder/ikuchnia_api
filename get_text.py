from datetime import datetime, timedelta, date
from json import load, dump
from pathlib import Path

from msgspec.json import decode
from requests import Session

from return_type import DayMeal

base_url = "https://ikuchnia.com.pl/klient/index.php"

path_to_secrets = Path("secret.json")


def get_data():
    with path_to_secrets.open() as f:
        secrets = load(f)
    data = {
        "login_email": secrets["login"],
        "pass": secrets["password"],
        "login": "Zaloguj",
    }
    return data


last_sid_path = Path("./sid.json")


def get_sid():
    # active for 10 min, 15 is invalid
    if last_sid_path.exists():
        with last_sid_path.open() as f:
            last_sid = load(f)
        if datetime.now() - datetime.fromisoformat(last_sid["timestamp"]) < timedelta(minutes=10):
            sid = last_sid["sid"]
        else:
            sid = None
    else:
        sid = None

    with Session() as session:
        if sid is not None:
            session.cookies.set("PHPSESSID", sid)
        else:
            session.request(method="POST", url=base_url, data=get_data())
            sid = session.cookies.get("PHPSESSID")
            new_sid = {"timestamp": datetime.now().isoformat(), "sid": sid}
            with last_sid_path.open(mode="w") as f:
                dump(new_sid, f)

    return sid


def get_day(day: date) -> DayMeal:
    data = {
        "do": "show_day",
        "day": day.isoformat(),
    }
    with Session() as session:
        session.cookies.set("PHPSESSID", get_sid())
        response = session.request(method="POST", url=base_url + "?module=kalendarz", data=data)
        result = decode(response.text, type=DayMeal)
    return result


def test():
    for day in range(1, 29):
        result = get_day(date(2024, 3, day))
        if result.day != day:
            print("Error: day is invalid")
            result.html = "..."  # for viewing purposes
            print(result)


if __name__ == '__main__':
    test()