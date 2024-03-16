from datetime import datetime, timedelta, date
from json import load, dump
from pathlib import Path

from msgspec.json import decode
from requests import Session

from parse_html import parse_meal_available_html, parse_meal_ordered_html
from return_type import RawMealsOrdered, RawMealsAvailable, MealsAvailable, MealsOrdered


class MealFetcher:
    base_url = "https://ikuchnia.com.pl/klient/"
    sid_path = Path("sid.json")

    def __init__(self, secrets_path: Path = Path("secret.json")):
        with secrets_path.open() as f:
            secrets = load(f)
        self.sid = None
        self.login_data = {
            "login_email": secrets["login"],
            "pass": secrets["password"],
            "login": "Zaloguj",
        }
        self.last_loaded_sid = datetime.now() - timedelta(minutes=20)
        self.check_sid()

    def check_sid(self):
        if datetime.now() - self.last_loaded_sid < timedelta(minutes=10):
            return

        if self.sid_path.exists():
            with self.sid_path.open() as f:
                last_sid = load(f)
            if datetime.now() - datetime.fromisoformat(last_sid["timestamp"]) < timedelta(minutes=10):
                self.sid = last_sid["sid"]
            else:
                self.sid = None
        else:
            self.sid = None

        if self.sid is not None:
            return

        with Session() as session:
            session.request(method="POST", url=self.base_url + "index.php", data=self.login_data)
            self.sid = session.cookies.get("PHPSESSID")
            with self.sid_path.open(mode="w") as f:
                dump({"timestamp": datetime.now().isoformat(), "sid": self.sid}, f)
        self.last_loaded_sid = datetime.now()

    def get_day(self, day: date, include_raw: bool = False) -> MealsOrdered:
        self.check_sid()
        data = {
            "do": "show_day",
            "day": day.isoformat(),
        }
        with Session() as session:
            session.cookies.set("PHPSESSID", self.sid)
            response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz", data=data)
            result = decode(response.text, type=RawMealsOrdered)
        return parse_meal_ordered_html(result, include_raw)

    def get_month(self, month: date) -> str:
        self.check_sid()
        data = {
            "do": "show_month",
            "month": f"{month.year}-{month.month}",
        }
        with Session() as session:
            session.cookies.set("PHPSESSID", self.sid)
            response = session.request(method="POST", url=self.base_url + "index.php?module=orderhistory", data=data)
        return response.text

    def get_styles(self) -> str:
        with Session() as session:
            response = session.request(method="GET", url=self.base_url + "css/styles.css")
        return response.text

    def get_meals(self, day: date, include_raw: bool) -> MealsAvailable:
        self.check_sid()
        data = {
            "do": "show_available",
            "day": day.isoformat(),
        }
        with Session() as session:
            session.cookies.set("PHPSESSID", self.sid)
            response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz", data=data)
            result = decode(response.text, type=RawMealsAvailable)
        return parse_meal_available_html(result, include_raw)


if __name__ == '__main__':
    meal_fetcher = MealFetcher()
