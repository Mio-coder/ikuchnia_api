from datetime import date
from pathlib import Path

from src import MealFetcher, file_login_getter


def test():
    meal_fetcher = MealFetcher(file_login_getter(Path("./secrets.json")))
    for day in range(1, 29):
        result = meal_fetcher.get_day_orders(date(2024, 3, day), True).raw
        if result.day != day:
            print("Error: day is invalid")
            result.html = "..."  # for viewing purposes
            print(result)
