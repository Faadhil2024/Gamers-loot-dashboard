import sqlite3
import time

DATABASE_NAME = "deals.db"

# 24 hours in seconds
CACHE_DURATION = 86400


def connect_db():
    """
    Connect to SQLite database.
    """

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    return conn


def create_table():
    """
    Create deals table if it does not exist.
    """

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            sale_price REAL,
            normal_price REAL,
            discount INTEGER,
            thumbnail TEXT,
            store TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()

    conn.close()


def save_deals(games):
    """
    Save fresh API deals into database.
    """

    conn = connect_db()

    cursor = conn.cursor()

    # Clear old deals
    cursor.execute("DELETE FROM deals")

    # Insert new deals
    for game in games:

        cursor.execute("""
            INSERT INTO deals (
                title,
                sale_price,
                normal_price,
                discount,
                thumbnail,
                store
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            game["title"],
            game["sale_price"],
            game["normal_price"],
            game["discount"],
            game["thumbnail"],
            game["store"]
        ))

    # Save refresh timestamp
    current_time = str(time.time())

    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('last_refresh', ?)
    """, (current_time,))

    conn.commit()

    conn.close()


def get_all_deals():
    """
    Fetch all deals from database.
    """

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM deals")

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def should_refresh():
    """
    Check if database is older than 24 hours.
    """

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT value
        FROM metadata
        WHERE key='last_refresh'
    """)

    result = cursor.fetchone()

    conn.close()

    # No timestamp yet
    if not result:
        return True

    last_refresh = float(result["value"])

    current_time = time.time()

    return (current_time - last_refresh) > CACHE_DURATION