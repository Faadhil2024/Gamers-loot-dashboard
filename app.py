from flask import Flask, render_template, request

# Import scraper
from scraper import get_game_deals

# Import database functions
from database import (
    create_table,
    save_deals,
    get_all_deals,
    should_refresh
)

app = Flask(__name__)

# Create database tables on startup
create_table()


@app.route("/")
def home():

    # ---------------------------------
    # REFRESH DATABASE EVERY 24 HOURS
    # ---------------------------------

    if should_refresh():

        print("Refreshing game deals from API...")

        fresh_games = get_game_deals()

        save_deals(fresh_games)

    else:

        print("Using cached database deals.")

    # ---------------------------------
    # LOAD GAMES FROM DATABASE
    # ---------------------------------

    games = get_all_deals()

    # Save original list
    all_games = games.copy()

    # Get unique stores
    stores = sorted(
        list(set(game["store"] for game in all_games))
    )

    # ---------------------------------
    # GET FILTER VALUES
    # ---------------------------------

    search_query = request.args.get(
        "search",
        ""
    ).lower()

    max_price = request.args.get(
        "max_price",
        ""
    )

    selected_store = request.args.get(
        "store",
        ""
    )

    sort_option = request.args.get(
        "sort",
        ""
    )

    # ---------------------------------
    # SEARCH FILTER
    # ---------------------------------

    if search_query:

        search_words = search_query.split()

        games = [
            game for game in games
            if any(
                word in game["title"].lower()
                for word in search_words
            )
        ]

    # ---------------------------------
    # MAX PRICE FILTER
    # ---------------------------------

    if max_price:

        try:

            max_price = float(max_price)

            games = [
                game for game in games
                if game["sale_price"] <= max_price
            ]

        except ValueError:
            pass

    # ---------------------------------
    # STORE FILTER
    # ---------------------------------

    if selected_store:

        games = [
            game for game in games
            if game["store"] == selected_store
        ]

    # ---------------------------------
    # SORTING
    # ---------------------------------

    if sort_option == "discount":

        games = sorted(
            games,
            key=lambda x: x["discount"],
            reverse=True
        )

    elif sort_option == "price_low":

        games = sorted(
            games,
            key=lambda x: x["sale_price"]
        )

    elif sort_option == "title":

        games = sorted(
            games,
            key=lambda x: x["title"]
        )

    # ---------------------------------
    # BEST DEAL FLAG
    # ---------------------------------

    for game in games:

        game["best_deal"] = (
            game["discount"] >= 85
            and game["sale_price"] > 5
        )

    # ---------------------------------
    # RENDER PAGE
    # ---------------------------------

    return render_template(
        "index.html",
        games=games,
        stores=stores
    )


if __name__ == "__main__":

    app.run(debug=True)