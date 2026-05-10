import requests

# Store mapping from CheapShark store IDs
STORE_NAMES = {
    "1": "Steam",
    "2": "GamersGate",
    "3": "GreenManGaming",
    "4": "Amazon",
    "5": "GameStop",
    "6": "Direct2Drive",
    "7": "GOG",
    "8": "Origin",
    "9": "Get Games",
    "10": "Shiny Loot",
    "11": "Humble Store",
    "12": "Desura",
    "13": "Uplay",
    "14": "IndieGameStand",
    "15": "Fanatical"
}


def get_steam_featured():
    """
    Fetch currently featured/on-sale games directly from Steam.
    No API key required. Returns real-time deals from Steam's front page.
    """

    url = "https://store.steampowered.com/api/featuredcategories"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Steam returns several categories — "specials" is the active sales
        specials = data.get("specials", {}).get("items", [])

        cleaned = []

        for game in specials:

            discount = game.get("discount_percent", 0)
            normal   = round(game.get("original_price", 0) / 100, 2)
            sale     = round(game.get("final_price",    0) / 100, 2)

            # Skip weak discounts and very cheap/free games
            if discount < 20 or normal < 3:
                continue

            thumbnail = (
                game.get("large_capsule_image")
                or game.get("header_image")
                or ""
            )

            if not thumbnail:
                continue

            cleaned.append({
                "title":        game.get("name", "Unknown Game"),
                "sale_price":   sale,
                "normal_price": normal,
                "discount":     discount,
                "thumbnail":    thumbnail,
                "store":        "Steam"
            })

        print(f"Steam API: fetched {len(cleaned)} featured deals.")
        return cleaned

    except Exception as e:
        print(f"Steam API error: {e}")
        return []


def get_cheapshark_deals():
    """
    Fetch game deals from CheapShark API.
    Filters to quality games only using Metacritic + Steam rating thresholds.
    """

    url = "https://www.cheapshark.com/api/1.0/deals"

    params = {
        "pageSize":    60,
        "sortBy":      "DealRating",
        "upperPrice":  60,
        "metacritic":  70,
        "steamRating": 70,
        "storeID":     "1,7,11,15",  # Steam, GOG, Humble, Fanatical
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        cleaned = []

        for game in data:

            if not game.get("thumb"):
                continue

            sale_price   = float(game.get("salePrice",   0) or 0)
            normal_price = float(game.get("normalPrice", 0) or 0)
            savings      = round(float(game.get("savings", 0)))

            # Skip weak discounts and low-value games
            if savings < 30:
                continue

            if normal_price < 4.99:
                continue

            cleaned.append({
                "title":        game.get("title", "Unknown Game"),
                "sale_price":   sale_price,
                "normal_price": normal_price,
                "discount":     savings,
                "thumbnail":    game.get("thumb"),
                "store":        STORE_NAMES.get(game.get("storeID"), "Unknown"),
            })

        print(f"CheapShark API: fetched {len(cleaned)} deals.")
        return cleaned

    except requests.exceptions.RequestException as error:
        print(f"CheapShark API error: {error}")
        return []


def get_game_deals():
    """
    Main function called by app.py.
    Merges Steam featured deals + CheapShark deals, deduplicates by title.
    Steam deals come first since they are the most current/relevant.
    """

    steam_deals      = get_steam_featured()
    cheapshark_deals = get_cheapshark_deals()

    seen   = set()
    merged = []

    # Steam first — most current, real-time
    for game in steam_deals + cheapshark_deals:

        # Normalise title for dedup check
        key = game["title"].strip().lower()

        if key not in seen:
            seen.add(key)
            merged.append(game)

    print(f"Total merged deals: {len(merged)}")
    return merged