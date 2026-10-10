import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "foodkeeper.json"

with DATA_PATH.open(encoding="utf-8") as data_file:
    FOODKEEPER_DATA = json.load(data_file)

FOODKEEPER_CATEGORIES = {
    category["ID"]: (
        f"{category['Category_Name']} - {category['Subcategory_Name']}"
        if category.get("Subcategory_Name")
        else category["Category_Name"]
    )
    for category in FOODKEEPER_DATA["categories"]
}

PRODUCTS = {}
for entry in FOODKEEPER_DATA["products"]:
    category = FOODKEEPER_CATEGORIES.get(entry["Category_ID"])
    if category is None:
        raise ValueError(f"Unknown FoodKeeper category for product {entry['ID']}")
    subtitle = entry.get("Name_subtitle")
    PRODUCTS[entry["ID"]] = {
        **entry,
        "display_name": f"{entry['Name']} — {subtitle}" if subtitle else entry["Name"],
        "category": category,
    }

FOOD_CATEGORIES = sorted(set(FOODKEEPER_CATEGORIES.values()), key=str.casefold)
PACKAGING_TYPES = [
    "Glass Container",
    "Aluminum Laminate",
    "Biodegradable Film",
    "Composite Film",
    "PET Plastic",
    "Paperboard",
    "Vacuum Pouch",
]


def get_options() -> dict:
    return {
        "food_categories": FOOD_CATEGORIES,
        "food_items": [
            {
                "id": product["ID"],
                "name": product["Name"],
                "description": product.get("Name_subtitle"),
                "display_name": product["display_name"],
                "category": product["category"],
            }
            for product in PRODUCTS.values()
        ],
        "packaging_types": PACKAGING_TYPES,
    }
