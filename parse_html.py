from json import load
from re import compile

from return_type import MealAvailable, MealsAvailable, RawMealsAvailable

# noinspection RegExpRedundantEscape
day_pattern = compile(r"<h4>(\d+) (Pon|Wto|Śr|Czw|Pią|Sob|Nie)<\/h4>(.*)$")
# noinspection RegExpRedundantEscape
entry_pattern = compile(
    r'<div class="dish-group"><i class="fa-solid fa-basket-shopping"><\/i> ([\w ęńł]+)<\/div>'
    r'<div class="dish-selected"><label data-danie-id="(\d+)" data-grupa-cenowa="(\d+)">'
    r'<input type="checkbox" name="danie_id" value="(\d+)" ((checked)?)>([\w ,]+)<\/label><\/div>')


def parse_meal_available_html(raw_meals: RawMealsAvailable, include_raw):
    html = raw_meals.html
    html = html.replace("\n", "")
    html = html.replace("\t", "")
    result = day_pattern.match(html)
    day_no = int(result.group(1))
    day_name = result.group(2)
    html = result.group(3)
    entries = entry_pattern.findall(html)
    meals = {}
    for entry in entries:
        print(entry)
        title = entry[0]
        danie_id_label = int(entry[1])
        grupa_cenowa = int(entry[2])
        danie_id = int(entry[3])
        selected = entry[4] == "checked"
        item = entry[5]
        meals[title] = MealAvailable(
            title,
            danie_id_label,
            danie_id,
            grupa_cenowa,
            selected,
            item
        )
    return MealsAvailable(
        day_no,
        day_name,
        meals,
        float(raw_meals.cena_przed),
        float(raw_meals.cena_po),
        raw_meals if include_raw else None
    )


def main():
    with open("meal_htmls.json") as f:
        data = load(f)
    for i, x in enumerate(data):
        print("data no.", i)
        print(parse_meal_available_html(x, ))


if __name__ == '__main__':
    main()
