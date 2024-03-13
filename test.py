from datetime import date

from get_text import MealFetcher


def test():
    meal_fetcher = MealFetcher()
    for day in range(1, 29):
        result = meal_fetcher.get_day(date(2024, 3, day))
        if result.day != day:
            print("Error: day is invalid")
            result.html = "..."  # for viewing purposes
            print(result)
