from datetime import date
from re import compile

from return_type import MealAvailable, MealsAvailable, RawMealsAvailable, \
    RawMealsOrdered, MealOrdered, MealsOrdered, ProjOrdered

html_day_pattern = compile(
    r"<h4>(\d+) (Pon|Wto|Śr|Czw|Pią|Sob|Nie|Mon|Tue|Wed|Thu|Fri|Sat|Sun)<\/h4>(.*)"
)
entry_pattern = compile(
    r'<div class="dish-group"><i class="fa-solid fa-basket-shopping"><\/i> ([^<]+)<\/div>'
    r'<div class="dish-selected"><label data-danie-id="(\d+)" data-grupa-cenowa="(\d+)">'
    r'<input type="checkbox" name="danie_id" value="(\d+)" (checked)?>([^<]+)<\/label><\/div>'
)

dish_pattern = compile(
    r"<div class=\"dish-group \"><i class=\"fas fa-utensils\"><\/i> ([^<]+)<\/div>"
    r"<div class=\"dish-selected (font-strike)?\">([^<]+)<\/div>"
)
edit_btn_pattern = compile(
    r'<div class="btn-group mb-3">'
    r'<button type="button" class="btn btn-success edit-button d-print-none" data-data="\d\d\d\d-\d\d-\d\d">'
    r'<i class="fa fa-pencil"></i> (Edytuj|Edit)'
    r'</button>'
    r'<button type="button" class="btn btn-outline-danger cancel-dish d-print-none" data-data="\d\d\d\d-\d\d-\d\d">'
    r'<i class="fa fa-trash"></i> (Odwołaj|Cancel)'
    r'</button>'
    r'</div>'
)
is_canceled_pattern = compile(
    r"<div class=\"btn-group mb-3\">"
    r"<button type=\"button\" class=\"btn btn-warning uncancel-dish d-print-none\" data-data=\"\d\d\d\d-\d\d-\d\d\">"
    r"<i class=\"fas fa-utensils\"></i> (Przywróć|Cancel)"
    r"</button>"
    r"</div>"
)
day_pattern = compile(
    r"\d\d (\w+)"
)
dish_name_translation = {
    "Zupa": "soup",
    "Danie mięsne": "meat_dish",
    "Danie wegetariańskie": "vegetarian_dish",
    "Danie dodatkowe": "bonus_dish",
    "Sok tłoczony na zimno": "juice",
    "Soup": "soup",
    "Meat dish": "meat_dish",
    "Vegetarian dish": "vegetarian_dish",
    # "Danie dodatkowe": "bonus_dish", not translated
    "Cold press juice": "juice",
}

# <div class="dish-group "><i class="fas fa-utensils"></i> Zupa</div><div class="dish-selected font-strike">Pomidorowa z makaronem </div><div class="btn-group mb-3"><button type="button" class="btn btn-warning uncancel-dish d-print-none" data-data="2024-03-15"><i class="fas fa-utensils"></i> Przywróć</button></div>

def parse_meal_available_html(raw_meals: RawMealsAvailable, order_date: date, include_raw: bool):
    """
    Parses HTML content of response for available meals

    :param raw_meals: raw meals from response
    :param include_raw: Whether to include the raw version of the response
    :return: available meals
    """
    html = raw_meals.html
    html = html.replace("\n", "")
    html = html.replace("\t", "")
    result = html_day_pattern.match(html)
    day_no = int(result.group(1))
    day_name = result.group(2)
    html = result.group(3)
    entries = entry_pattern.findall(html)
    meals = {
        "soup": None,
        "meat_dish": None,
        "vegetarian_dish": None,
        "bonus_dish": None,
        "juice": None
    }
    for entry in entries:
        title = entry[0]
        danie_id_label = int(entry[1])
        grupa_cenowa = int(entry[2])
        danie_id = int(entry[3])
        selected = entry[4] == "checked"
        item = entry[4]
        meals[dish_name_translation[title]] = MealAvailable(
            title,
            danie_id_label,
            danie_id,
            grupa_cenowa,
            selected,
            item
        )
    return MealsAvailable(
        order_date,
        day_name,
        meals["soup"],
        meals["meat_dish"],
        meals["vegetarian_dish"],
        meals["bonus_dish"],
        meals["juice"],
        float(raw_meals.cena_przed),
        float(raw_meals.cena_po),
        raw_meals if include_raw else None
    )


def parse_proj_ordered(raw_proj):
    """Parses proj to more usable types"""
    return ProjOrdered(
        raw_proj.do_kiedy_zamowic_dzis,
        raw_proj.do_kiedy_zamowic,
        raw_proj.sposob_zamawiania,
        raw_proj.pokaz_dania == "yes",
        int(raw_proj.ID),
        raw_proj.guzik_edytuj,
        raw_proj.rezygnacja
    )


def parse_meal_ordered_html(raw_order: RawMealsOrdered, include_raw: bool = False) -> MealsOrdered:
    """
    Parses HTML content of response for ordered meals

    :param raw_order: Raw meals data from the response
    :param include_raw: Whether to include the raw version of the response
    :return: Ordered meals
    """
    html = raw_order.html
    html = html.replace("\n", "")
    html = html.replace("\t", "")
    matches = dish_pattern.match(html)
    meals = []
    meals_matches = matches.groups()
    meals_matches = (meals_matches,) if not isinstance(meals_matches[0], tuple) else meals_matches
    for match in meals_matches:
        meals.append(MealOrdered(
            match[0],
            match[2],
        ))
        # match[1] == "font-strike" => is canceled
    # date we know
    can_edit = edit_btn_pattern.match(html) is not None
    is_canceled = is_canceled_pattern.match(html) is not None
    day = day_pattern.match(raw_order.date).group(1)
    order_date = date.fromisoformat(raw_order.sql)
    proj = list(map(
        parse_proj_ordered,
        raw_order.proj
    ))
    return MealsOrdered(
        meals,
        can_edit,
        is_canceled,
        day,
        order_date,
        raw_order.blokada_zamawiania,
        proj,
        raw_order if include_raw else None
    )


if __name__ == '__main__':
    pass
