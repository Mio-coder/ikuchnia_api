from datetime import datetime, timedelta, date
from json import load
from pathlib import Path
from typing import NoReturn

from msgspec.json import decode, encode
from requests import Session

from parse_html import parse_meal_available_html, parse_meal_ordered_html
from return_type import RawMealsOrdered, RawMealsAvailable, MealsAvailable, MealsOrdered, Sid


class MealFetcher:
    """
    Client for iKuchnia internal api

    :ivar base_url: Base URL for the iKuchnia internal API
    :ivar sid_path: Path to store the session ID
    :ivar sid: Session ID
    """

    base_url = "https://ikuchnia.com.pl/klient/"
    sid_path = Path("sid.json")
    sid: Sid
    """Session ID"""

    def __init__(self, secrets_path: Path = Path("secret.json")):
        """
        Initializes the MealFetcher with secrets path

        :param secrets_path: Path to the secrets file (default: 'secret.json').
        """
        with secrets_path.open() as f:
            secrets = load(f)
        self.login_data = {
            "login_email": secrets["login"],
            "pass": secrets["password"],
            "login": "Zaloguj",
        }
        self.sid = Sid(datetime.now() - timedelta(1), "")
        self.check_sid()

    def check_sid(self) -> NoReturn:
        """
        Ensures that the session ID is active and
        stores it in file self.sid_path
        """

        need_refresh = self.sid.sid == "" or datetime.now() - self.sid.timestamp > timedelta(minutes=10)

        if not need_refresh:
            return

        if self.sid_path.exists():
            with self.sid_path.open() as f:
                last_sid = decode(f.read(), type=Sid)
            if datetime.now() - last_sid.timestamp < timedelta(minutes=10):
                self.sid = last_sid
                need_refresh = False

        if need_refresh:
            with Session() as session:
                session.request(method="POST", url=self.base_url + "index.php", data=self.login_data)
                self.sid = Sid(datetime.now(), session.cookies.get("PHPSESSID"))
                need_refresh = False

        if need_refresh:
            raise ValueError("Could not get sid")

        with self.sid_path.open(mode="wb") as f:
            f.write(encode(self.sid))

    def get_day(self, day: date, include_raw: bool = False) -> MealsOrdered:
        """
        Get ordered meals for a day

        :param day: The day to get meals from
        :param include_raw: Whether to include not parsed version of response
        :return: ordered meals
        """
        self.check_sid()
        data = {
            "do": "show_day",
            "day": day.isoformat(),
        }
        with Session() as session:
            self.sid.set(session)
            response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz", data=data)
            result = decode(response.text, type=RawMealsOrdered)
        return parse_meal_ordered_html(result, include_raw)

    def get_month(self, month: date) -> str:
        """
        Get HTML for orders for month,
        excluding days without meals
        Call :self:`get_styles <get_styles>` for stylesheets

        :param month: the month to get meals for
        :return: html
        """
        self.check_sid()
        data = {
            "do": "show_month",
            "month": f"{month.year}-{month.month}",
        }
        with Session() as session:
            self.sid.set(session)
            response = session.request(method="POST", url=self.base_url + "index.php?module=orderhistory", data=data)
        return response.text

    def get_styles(self) -> str:
        """
        Get style sheets for rendering month HTML

        :return: stylesheet
        """
        with Session() as session:
            response = session.request(method="GET", url=self.base_url + "css/styles.css")
        return response.text

    def get_meals(self, day: date, include_raw: bool) -> MealsAvailable:
        """
        Get available meals for a day

        :param day: Date to get meals for
        :param include_raw: Whether to include not parsed version of response
        :return: Available meals
        """
        self.check_sid()
        data = {
            "do": "show_available",
            "day": day.isoformat(),
        }
        with Session() as session:
            self.sid.set(session)
            response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz", data=data)
            result = decode(response.text, type=RawMealsAvailable)
        return parse_meal_available_html(result, include_raw)


if __name__ == '__main__':
    meal_fetcher = MealFetcher()
