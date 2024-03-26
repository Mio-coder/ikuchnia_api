from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Callable

from msgspec.json import decode, encode
from requests import Session

from parse_html import parse_meal_available_html, parse_meal_ordered_html
from return_type import RawMealsOrdered, RawMealsAvailable, MealsAvailable, MealsOrdered, Sid


def file_login_getter(file: Path):
    """
    function that returns secrets stored in file
    not recommended for sensitive data
    """

    def getter():
        with file.open() as f:
            return decode(f.read(), type=tuple)

    return getter


class MealFetcher:
    """
    Client for iKuchnia internal api
    """

    base_url = "https://ikuchnia.com.pl/klient/"

    def __init__(self, secrets_getter: Callable[[], tuple[str, str]], sid_path: Path = Path("./sid.json")):
        """
        Initializes the MealFetcher with secrets getter function
        """
        self.secrets_getter = secrets_getter
        self.sid_path = sid_path
        self.sid = Sid(datetime.now(), "")
        self.check_sid(True)

    def check_sid(self, force_refresh: bool = False) -> bool:
        """
        Ensures that the session ID is active and
        stores it in file self.sid_path
        returns if self.sid has changed
        if force_refresh is True, always refreshes the sid
        """
        need_refresh = self.sid.sid == "" or datetime.now() - self.sid.timestamp > timedelta(minutes=10)

        if need_refresh and not force_refresh and self.sid_path.exists():
            with self.sid_path.open() as f:
                last_sid = decode(f.read(), type=Sid)
            if datetime.now() - last_sid.timestamp < timedelta(minutes=10):
                self.sid = last_sid
                need_refresh = False

        if not need_refresh and not force_refresh:
            return False

        if need_refresh or force_refresh:
            with Session() as session:
                login = self.secrets_getter()
                session.request(method="POST", url=self.base_url + "index.php", data={
                    "login_email": login[0],
                    "pass": login[1],
                    "login": "Zaloguj",
                })
                self.sid = Sid(datetime.now(), session.cookies.get("PHPSESSID"))
                need_refresh = False

        with self.sid_path.open(mode="wb") as f:
            f.write(encode(self.sid))

        return True

    def get_day_orders(self, day: date, include_raw: bool = False) -> MealsOrdered:
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

    def get_month_orders(self, month: date) -> str:
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

    def get_day_available(self, day: date, include_raw: bool = False) -> MealsAvailable:
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
        return parse_meal_available_html(result, day, include_raw)

    def send_dishes(self, meals: MealsAvailable):
        """
        Orders meals based on selected variable of MealAvailable.
        if any other field is modified it may through an error
        """
        original_dishes = self.get_day_available(meals.date)
        different = []
        for orig, order in zip(original_dishes.dishes.keys(), meals.dishes.keys()):
            if orig.selected != order.selected:
                different.append(order)
        print(different)
        self.check_sid()
        with Session() as session:
            self.sid.set(session)
            for diff in different:
                data = {
                    "do": "wstaw_posilek",
                    "data": meals.date.isoformat(),
                    "danie": diff.meal_id,
                    "state": diff.selected,
                }
                # when not submitted this does nothing
                response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz",
                                           data=data)
                if response.text.startswith("<!DOCTYPE html>"):
                    raise ValueError("Invalid sid")
            data = {
                "do": "save_dishes",
            }
            for i, diff in enumerate(different):
                data[f"arr[{i}][name]"] = "danie_id"
                data[f"arr[{i}][value]"] = diff.meal_id
            data[f"arr[{len(different)}][name]"] = "date"
            data[f"arr[{len(different)}][name]"] = meals.date.isoformat()
            response = session.request(method="POST", url=self.base_url + "index.php?module=kalendarz", data=data)
            # result = response.json()
            # we get day_no and date


if __name__ == '__main__':
    meal_fetcher = MealFetcher(
        file_login_getter(Path("./secret.json"))
    )
