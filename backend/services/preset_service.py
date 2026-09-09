import re
from typing import Any, Dict, List, Optional

FILES: Dict[str, Dict[str, List[str]]] = {
    "bakery": {
        "set-01": "cheese-danish eclair cream-puff swiss-roll red-velvet-cake sponge-cake cheesecake-cup chocolate-truffle shortbread-biscuit pretzel garlic-bread-loaf brioche scone palmier custard-tart".split(),
        "set-02": "bread-loaf croissant cupcake chocolate-cake doughnut muffin cookies cinnamon-roll baguette puff-pastry fruit-tart brownie bread-bun macarons fruit-pie".split(),
    },
    "burger": {
        "set-01": "fish-burger spicy-chicken-burger bacon-burger mushroom-burger paneer-burger mini-sliders loaded-fries cheese-fries potato-wedges mozzarella-sticks chicken-tenders corn-dog coleslaw lemonade chocolate-brownie".split(),
        "set-02": "classic-burger cheeseburger chicken-burger double-burger vegetable-burger french-fries onion-rings chicken-nuggets hot-dog grilled-wrap fried-chicken milkshake soft-drink dipping-sauce ice-cream-sundae".split(),
    },
    "cafe": {
        "set-01": "cold-brew hot-chocolate green-tea lemon-tea masala-chai club-sandwich garlic-toast pancakes waffles bagel apple-pie chocolate-tart banana-bread fruit-bowl nachos".split(),
        "set-02": "cappuccino latte espresso iced-coffee mocha tea croissant grilled-sandwich muffin cheesecake brownie cookies doughnut vegetable-wrap french-fries".split(),
    },
    "grocery": {
        "set-01": "oranges grapes watermelon cucumber bell-peppers spinach cheese butter flour sugar salt lentils pasta-pack biscuits dishwashing-liquid".split(),
        "set-02": "apples bananas tomatoes potatoes onions carrots milk eggs bread rice cooking-oil cereal orange-juice yoghurt detergent".split(),
    },
    "ice-cream": {
        "set-01": "vanilla-ice-cream chocolate-ice-cream strawberry-ice-cream mango-ice-cream butterscotch-ice-cream black-currant-ice-cream pistachio-ice-cream cookies-and-cream-ice-cream kulfi ice-cream-sundae ice-cream-cone ice-cream-cup brownie-with-ice-cream banana-split milkshake".split(),
        "set-02": "vanilla-ice-cream chocolate-ice-cream strawberry-ice-cream mango-ice-cream mint-ice-cream waffle-cone ice-cream-sundae ice-cream-sandwich popsicle soft-serve chocolate-syrup-ice-cream sprinkle-ice-cream waffle-bowl banana-split milkshake".split(),
    },
    "other": {
        "set-01": "burger pizza sandwich ice-cream coffee t-shirt shoes handbag wristwatch headphones haircut beard-trim head-massage gift-box flower-bouquet".split(),
    },
    "pizza": {
        "set-01": "bbq-chicken-pizza hawaiian-pizza four-cheese-pizza paneer-tikka-pizza spicy-sausage-pizza seafood-pizza spinach-pizza corn-pizza olive-pizza stuffed-crust-pizza cheese-balls mozzarella-sticks potato-wedges caesar-salad chocolate-lava-cake".split(),
        "set-02": "margherita-pizza pepperoni-pizza vegetable-pizza cheese-pizza chicken-pizza mushroom-pizza garlic-bread breadsticks pizza-slice calzone pasta chicken-wings french-fries soft-drink dipping-sauce".split(),
    },
    "restaurant": {
        "set-01": "chicken-curry mutton-curry prawn-fry chicken-kebab chilli-chicken gobi-manchurian dal-tadka jeera-rice chapati paratha pulao chicken-soup vegetable-cutlet spring-roll gulab-jamun".split(),
        "set-02": "chicken-biryani grilled-chicken butter-naan paneer-curry vegetable-fried-rice noodles masala-dosa idli samosa tandoori-chicken fish-curry vegetarian-thali pasta vegetable-soup mixed-salad".split(),
    },
    "retail-store": {
        "set-01": "formal-shirt jacket dress sandals slippers belt cap bracelet necklace smartphone-case bluetooth-speaker umbrella cushion wall-clock shopping-basket".split(),
        "set-02": "t-shirt jeans sneakers handbag wristwatch sunglasses perfume headphones backpack wallet water-bottle toy notebook table-lamp coffee-mug".split(),
    },
    "salon": {
        "set-01": "haircut beard-trim child-haircut hair-wash hair-styling hair-coloring facial cleanup manicure pedicure head-massage hair-spa threading waxing bridal-makeup".split(),
        "set-02": "mens-haircut womens-haircut child-haircut beard-trim clean-shave hair-colouring hair-straightening hair-styling facial face-cleanup head-massage hair-spa manicure pedicure body-massage".split(),
    },
}


def polished_name(slug: str) -> str:
    custom_names: Dict[str, str] = {
        "bbq": "BBQ",
        "idli": "Idli",
        "gobi": "Gobi",
        "jeera": "Jeera",
        "kulfi": "Kulfi",
        "mens": "Men's",
        "womens": "Women's",
        "t": "T",
    }
    parts = slug.split("-")
    result = " ".join(custom_names.get(w, w.capitalize()) for w in parts)
    if result == "T Shirt":
        return "T-Shirt"
    return result


def food_type_for(asset_type: str, slug: str) -> Optional[str]:
    if asset_type in ("retail-store", "salon"):
        return None
    if asset_type == "other" and not re.search(r"(burger|pizza|sandwich|ice-cream|coffee)", slug):
        return None
    if asset_type == "grocery" and re.search(r"(dishwashing|detergent)", slug):
        return None
    if re.search(
        r"(chicken|mutton|prawn|fish|bacon|sausage|seafood|pepperoni|hawaiian|egg|classic-burger|cheeseburger|double-burger|hot-dog|corn-dog|fried-chicken)",
        slug,
    ):
        return "non-veg"
    return "veg"


def category_for(asset_type: str, slug: str) -> str:
    if asset_type == "salon":
        if re.search(r"(manicure|pedicure)", slug):
            return "Nail Care"
        if re.search(r"(facial|cleanup|threading|waxing|makeup)", slug):
            return "Skin & Beauty"
        if re.search(r"(massage|spa)", slug):
            return "Wellness"
        return "Hair & Grooming"
    if asset_type == "retail-store":
        if re.search(r"(shirt|jacket|dress|jeans)", slug):
            return "Clothing"
        if re.search(r"(sandals|slippers|sneakers)", slug):
            return "Footwear"
        if re.search(r"(case|speaker|headphones)", slug):
            return "Electronics"
        if re.search(r"(cushion|clock|lamp|mug|bottle|umbrella)", slug):
            return "Home & Lifestyle"
        return "Accessories"
    if asset_type == "grocery":
        if re.search(r"(apple|banana|orange|grape|watermelon|tomato|potato|onion|carrot|cucumber|pepper|spinach)", slug):
            return "Fresh Produce"
        if re.search(r"(milk|egg|cheese|butter|yoghurt)", slug):
            return "Dairy & Eggs"
        if re.search(r"(dishwashing|detergent)", slug):
            return "Household"
        return "Pantry"
    if asset_type == "bakery":
        if re.search(r"(bread|loaf|brioche|baguette|bun|pretzel)", slug):
            return "Breads"
        if re.search(r"(cake|cheesecake|truffle|brownie)", slug):
            return "Cakes"
        if re.search(r"(biscuit|cookies|shortbread)", slug):
            return "Biscuits"
        return "Pastries"
    if asset_type == "cafe":
        if re.search(r"(coffee|brew|chocolate|tea|chai|cappuccino|latte|espresso|mocha)", slug):
            return "Beverages"
        if re.search(r"(pie|tart|cake|brownie|cookies|doughnut|muffin)", slug):
            return "Desserts"
        return "Cafe Bites"
    if asset_type == "ice-cream":
        if re.search(r"(sundae|split|brownie)", slug):
            return "Sundaes"
        if re.search(r"(cone|cup|bowl|sandwich|popsicle|serve)", slug):
            return "Ice Cream Treats"
        if re.search(r"(milkshake)", slug):
            return "Shakes"
        return "Scoop Flavours"
    if asset_type == "pizza":
        if "pizza" in slug:
            return "Pizzas"
        if re.search(r"(drink)", slug):
            return "Drinks"
        if re.search(r"(cake)", slug):
            return "Desserts"
        return "Sides"
    if asset_type == "burger":
        if "burger" in slug or "slider" in slug:
            return "Burgers"
        if re.search(r"(lemonade|drink|milkshake)", slug):
            return "Drinks"
        if re.search(r"(brownie|sundae)", slug):
            return "Desserts"
        return "Sides"
    if asset_type == "restaurant":
        if re.search(r"(rice|chapati|paratha|pulao|naan|biryani)", slug):
            return "Rice & Breads"
        if re.search(r"(jamun)", slug):
            return "Desserts"
        if re.search(r"(kebab|fry|cutlet|roll|samosa)", slug):
            return "Starters"
        return "Main Course"
    if asset_type == "other":
        if re.search(r"(burger|pizza|sandwich|ice-cream|coffee)", slug):
            return "Food & Drinks"
        if re.search(r"(haircut|trim|massage)", slug):
            return "Services"
        return "Products"
    return "Menu"


def resolve_asset_type(business_type: str, description: Optional[str] = None) -> str:
    normalized = "retail-store" if business_type == "retail" else "ice-cream" if business_type == "ice_cream" else business_type
    if normalized != "other" and normalized in FILES:
        return normalized
    value = (description or "").lower()
    if re.search(r"(salon|hair|beauty|spa|barber)", value):
        return "salon"
    if re.search(r"(bakery|cake|bread|pastry)", value):
        return "bakery"
    if re.search(r"(pizza)", value):
        return "pizza"
    if re.search(r"(burger|fast food)", value):
        return "burger"
    if re.search(r"(cafe|coffee|tea)", value):
        return "cafe"
    if re.search(r"(restaurant|food|dining)", value):
        return "restaurant"
    if re.search(r"(grocery|supermarket|food store)", value):
        return "grocery"
    if re.search(r"(ice cream|dessert)", value):
        return "ice-cream"
    if re.search(r"(retail|shop|fashion|clothing|electronics)", value):
        return "retail-store"
    return "other"


def get_all_menu_presets() -> List[Dict[str, Any]]:
    presets: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for asset_type, sets in FILES.items():
        for set_key, names in sets.items():
            for idx, slug in enumerate(names):
                duplicate_key = slug.replace("colouring", "coloring")
                if duplicate_key in seen:
                    continue
                seen.add(duplicate_key)
                presets.append({
                    "id": f"{asset_type}-{duplicate_key}",
                    "name": polished_name(slug),
                    "imagePath": f"/onboarding-menu/{asset_type}/{set_key}/{str(idx + 1).zfill(2)}-{slug}.jpg",
                    "category": category_for(asset_type, slug),
                    "foodType": food_type_for(asset_type, slug),
                })
    return presets


_ALL_PRESETS_CACHE: List[Dict[str, Any]] = get_all_menu_presets()


def get_menu_presets_for_business_type(
    business_type: str, description: Optional[str] = None
) -> List[Dict[str, Any]]:
    asset_type = resolve_asset_type(business_type, description)
    prefix = f"{asset_type}-"
    return [p for p in _ALL_PRESETS_CACHE if p["id"].startswith(prefix)]
