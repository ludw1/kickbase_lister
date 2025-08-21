from auth import login
from call_api import call_api
import logging
import json
from os import path
import requests
from datetime import datetime, timedelta
from tabulate import tabulate
from collections import defaultdict
from parse_html import style_table
import webbrowser
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
""" 1. Find every manager in the league, get their team and teamvalue and points.
    2. Calculate the profit/loss.
    3. Calculate their current cash value.
    4. See how many 500k players, player with biggest market value.
    5. Perhaps add expected points.
"""


class UserTable:
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.team_value = 0
        self.team = []
        self.total_points = 0
        self.placement = 0
        self.matchday_wins = 0
        self.tv_change = (
            0  # Change of the team value between last match day and current matchday
        )
        self.pnl = 0
        self.bigboy = ""  # Name of player with highest market value
        self.bigboy_value = 0
        self.half_million_players = 0
        self.expected_points = 0
        self.biggest_overpay = 0
        self.biggest_overpay_player = ""
        self.biggest_lose = 0
        self.biggest_lose_player = ""
        self.biggest_win = 0
        self.biggest_win_player = ""

    def return_data(self) -> dict:
        # Make representation easier to use with tabulate
        data_dict = {
            "Name": self.name
            + f'<img src="https://cdn.kickbase.com/files/users/{self.user_id}/0" alt="" border=3 height=100 width=100>',
            "Teamwert": format_numbers(self.team_value)
            + f" ({format_numbers(self.tv_change)}"
            + "⬆️)"
            if self.tv_change > 0
            else format_numbers(self.team_value)
            + f" ({format_numbers(self.tv_change)}"
            + "⬇️)",
            "Gesamtpunkte": self.total_points,
            "Matchday-Siege": self.matchday_wins,
            # "pnl" : self.pnl, # Kann man kalkulierten mit dem Anfangswert und Trades aber cba
            "Big Boy": self.bigboy + f" ({format_numbers(self.bigboy_value)})",
            "500k Spieler": self.half_million_players,
            # "expected_points" : self.expected_points, # Wird vielleicht mal implementiert mit player_analyze
            "Größter overpay Spieler": self.biggest_overpay_player
            + f" ({format_numbers(self.biggest_overpay)})",
            "Größter Verlust Spieler": self.biggest_lose_player
            + f" ({format_numbers(self.biggest_lose)})",
            "Größter Gewinn Spieler": self.biggest_win_player
            + f" ({format_numbers(self.biggest_win)})",
        }
        return data_dict

    def __repr__(self):
        return f"UserTable({self.user_id}, {self.name}, {self.team_value}, {self.total_points}, {self.placement}, {self.matchday_wins}, {self.tv_change}, {self.pnl}, {self.bigboy}, {self.bigboy_value}, {self.half_million_players}, {self.expected_points}, {self.biggest_overpay}, {self.biggest_overpay_player}, {self.biggest_lose}, {self.biggest_lose_player}, {self.biggest_win}, {self.biggest_win_player})"

    def __str__(self):
        return f"UserTable({self.user_id}, {self.name}, {self.team_value}, {self.total_points}, {self.placement}, {self.matchday_wins}, {self.tv_change}, {self.pnl}, {self.bigboy}, {self.bigboy_value}, {self.half_million_players}, {self.expected_points}, {self.biggest_overpay}, {self.biggest_overpay_player}, {self.biggest_lose}, {self.biggest_lose_player}, {self.biggest_win}, {self.biggest_win_player})"


def format_numbers(number: int | float) -> str:
    # Only keep first four relevant digits for numbers in the hundred million
    # 3 digits for 10 million
    # 2 digits for 1 million
    # all 6 digits for hundred thousands
    # remove any number behind the comma
    if abs(number) >= 1_000_000:
        return f"{number / 10**6:.1f}M"
    elif abs(number) < 1000:
        return f"{number:.1f}"
    return f"{number / 1000:.1f}K"


def get_users(token: str, league_id: str) -> dict[int, UserTable]:
    """
    Get all users and their IDs in the league.
    """
    url = f"https://api.kickbase.com/v4/leagues/{league_id}/overview?includeManagersAndBattles=true"
    data = call_api(token, url, {"us": []})
    user_table = {}
    for user in data.get("us", []):
        user_table[user["i"]] = UserTable(user_id=user["i"], name=user["n"])
    return user_table


def get_user_stats(token: str, league_id: str, user_id: int) -> dict[str, int]:
    """
    ### Get the user stats for a specific user in the league.
    """
    url = (
        f"https://api.kickbase.com/v4/leagues/{league_id}/managers/{user_id}/dashboard"
    )
    try:
        data = call_api(
            token, url, {"mdw": 0, "pl": 0, "tp": 0, "tv": 0}
        )  # MatchDayWins, Placement, TotalPoints, TeamValue
        return data
    except Exception as e:
        raise Exception(f"Error fetching user stats: {e}")


def get_user_team(token: str, league_id: str, user_id: int) -> dict:
    """
    ### Get the team of a specific user in the league.
    """
    url = f"https://api.kickbase.com/v4/leagues/{league_id}/managers/{user_id}/squad"
    try:
        data = call_api(token, url, {"it": []})  # Players in the team
        return data
    except Exception as e:
        raise Exception(f"Error fetching user team: {e}")


def get_transfers(token: str, league_id: int) -> list:
    """### Get all transfers of all users in a league.

    Args:
        token (str): The user's kkstrauth token.
        league_id (str): The league ID.

    Returns:
        dict: A dictionary containing the user's players.
    """
    start_point = 0
    user_transfers = []

    while True:
        query_params = f"?max=26&start={start_point}"
        url = f"https://api.kickbase.com/v4/leagues/{league_id}/activitiesFeed/{query_params}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": f"kkstrauth={token};",
        }

        ### Send GET request to get the next 26 entries
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error fetching transfers: {e}")
        ### Filter transfers where "t" == 15
        filtered_transfers = [
            entry for entry in response.json().get("af", []) if entry.get("t") == 15
        ]
        user_transfers += filtered_transfers

        ### Check if there are more entries to fetch
        if not response.json().get("af"):
            break

        start_point += 26

    return user_transfers


def get_player_statistics(token: str, league_id: int, player_id: int):
    """
    Get the statistics of a given player.
    """
    url = f"https://api.kickbase.com/v4/competitions/1/players/{player_id}?leagueId={league_id}"
    return call_api(token, url)


def get_player_marketvalue(token: str, player_id: int):
    url = f"https://api.kickbase.com/v4/competitions/1/players/{player_id}/marketValue/365"
    return call_api(token, url)["it"]


def get_player_marketvalue_date(token: str, player_id: int, start_date: str):
    url = f"https://api.kickbase.com/v4/competitions/1/players/{player_id}/marketValue/365"
    data = call_api(token, url)["it"]
    ### Set the price to the START_DATE value in the player_marketvalues list
    price = 0
    for marketValue in data:
        market_value_date = julian_to_date(marketValue["dt"])
        yesterday = datetime.strftime(datetime.today() - timedelta(days=1), "%d.%m.%Y")
        if market_value_date == start_date or (
            market_value_date == yesterday and price == 0
        ):
            price = marketValue["mv"]
    if price == 0:
        logging.info("No price found?")
        logging.info(data)
        logging.info(start_date)
    return price


def julian_to_date(julian_date: int) -> str:
    """Convert a Julian date to a standard date format (YYYY-MM-DD)."""
    reference_date = datetime(1970, 1, 1)
    converted_date = reference_date + timedelta(days=julian_date)
    return converted_date.strftime("%d.%m.%Y")


def get_turnovers(
    user_token: str,
    selected_league: int,
    league_start: str,
    user_table: dict[int, UserTable],
    update_turnovers: bool,
) -> None:
    """### Retrieves all turnovers in the league.

    Args:
        user_token (str): The user's kkstrauth token.
        selected_league (object): The league the user wants to get data from for the frontend.
    """
    logging.info("Getting turnovers...")

    final_turnovers = []

    ### Load existing transfers from all_transfers.json which were saved in earlier runs
    all_transfers_path = "all_transfers.json"

    all_transfers = []  # Initialize as empty list first

    ### Check if all_transfers.json exists and load it
    if path.exists(all_transfers_path):
        try:
            with open(all_transfers_path, "r") as f:
                all_transfers = json.load(f)
            logging.debug(
                f"Loaded {len(all_transfers)} existing transfers from all_transfers.json"
            )
        except json.JSONDecodeError:
            logging.warning(
                f"The file {all_transfers_path} is empty or contains invalid JSON. Initializing all_transfers as an empty list."
            )
    else:
        logging.debug(
            f"The file {all_transfers_path} does not exist. Initializing all_transfers as an empty list."
        )

    ### Get new transfers from the API
    new_transfers = get_transfers(user_token, selected_league)
    logging.debug(f"Found {len(new_transfers)} current transfers from the API")

    ### Append only new transfers (ignoring duplicates)
    current_transfer_ids = {
        item["i"] for item in all_transfers
    }  # Set of existing transfer IDs
    for transfer in new_transfers:
        if transfer["i"] not in current_transfer_ids:  # Check if the transfer is new
            all_transfers.append(transfer)
            current_transfer_ids.add(
                transfer["i"]
            )  # Update the set to include the new transfer

    ### Sort transfers by date after appending new ones
    all_transfers.sort(key=lambda x: datetime.fromisoformat(x["dt"].replace("Z", "")))

    logging.info(f"Total transfers after appending new ones: {len(all_transfers)}")

    ### Save updated transfers back to all_transfers.json
    with open("all_transfers.json", "w") as f:
        json.dump(all_transfers, f, indent=4)
    logging.info("Updated all_transfers.json with new transfers")

    ### Process the transfers as usual
    transfers = []

    logging.info("Processing transfers...")
    if path.exists("transfers_form.json") and not update_turnovers:
        with open("transfers_form.json", "r") as f:
            transfers = json.load(f)
    else:
        if path.exists("transfers_form.json"):
            with open("transfers_form.json", "r") as f:
                transfers = json.load(f)
        ### Process each transfer item
        for item in all_transfers:
            user = None
            trade_partner = None
            ### Determine the transfer type based on the type and metadata
            if item["t"] == 15:
                if "slr" in item["data"] and "byr" in item["data"]:
                    transfer_type = "sell"
                    user = item["data"]["slr"]
                    trade_partner = item["data"]["byr"]
                elif "slr" in item["data"]:
                    transfer_type = "sell"
                    user = item["data"]["slr"]
                    trade_partner = "Kickbase"
                elif "byr" in item["data"]:
                    transfer_type = "buy"
                    user = item["data"]["byr"]
                    trade_partner = "Kickbase"
                else:
                    transfer_type = "unknown"
            else:
                transfer_type = "unknown"
            logging.info(f"Fetch statistics of player {item['data']['pi']}.")
            ### Search the stats of the given player ID to fill the missing attributes for the player
            player_stats = get_player_statistics(
                user_token, selected_league, item["data"]["pi"]
            )
            logging.info(f"Stats fetched for player {item['data']['pi']}")
            ### Create a custom json dict for every transfer
            new_transfer = {
                "date": item["dt"],
                "type": transfer_type,
                "user": user,
                "tradePartner": trade_partner,
                "price": item["data"]["trp"],
                "playerId": item["data"]["pi"],
                "teamId": item["data"]["tid"],
                "firstName": player_stats.get("fn", None),
                "lastName": player_stats["ln"],
            }
            if not any([d["date"] == item["dt"] for d in transfers]):
                new_transfer["marketPrice"] = get_player_marketvalue_date(
                    user_token,
                    item["data"]["pi"],
                    datetime.strptime(item["dt"], "%Y-%m-%dT%H:%M:%SZ").strftime(
                        "%d.%m.%Y"
                    ),
                )
                transfers.append(new_transfer)
                logging.info(f"Latest transfer: {transfers[-1]}")
        ### Removes duplicates given by the API (probably not needed since v4)
        transfers = list({frozenset(item.items()): item for item in transfers}.values())
        with open("transfers_form.json", "w") as f:
            json.dump(transfers, f, indent=4)

    logging.info("Transfers processed successfully.")
    turnovers = []
    if not update_turnovers and path.exists("turnovers.json"):
        with open("turnovers.json", "r") as f:
            final_turnovers = json.load(f)
    else:
        ### Iterate over every element in the "transfers" list (where "i" is the index) and save it to "buy_transfer"
        for i, buy_transfer in enumerate(transfers):
            ### Skip if the transfer is type "sell"
            if buy_transfer["type"] == "sell":
                continue

            ### This nested loop iterates over the remaining transfers (starting from the current buy transfer).
            ### It compares each of these transfers with the current buy transfer
            for sell_transfer in transfers[i:]:
                if sell_transfer["type"] == "buy":
                    continue

                ### This condition checks if the player ID of the current sell transfer matches the player ID of the current buy transfer.
                ### If there is a match, it means a corresponding buy-sell pair is found.
                if sell_transfer["playerId"] == buy_transfer["playerId"]:
                    turnovers.append((buy_transfer, sell_transfer))
                    break

        ### Revenue generated by randomly assigned players
        for transfer in transfers:
            ### Skip buy transfers
            if transfer["type"] == "buy":
                continue

            ### This condition checks if the current sell transfer is not already part of a buy-sell pair in the turnovers list.
            if transfer not in [turnover[1] for turnover in turnovers]:
                ### Loop through all marketValues of the player until the "day" matches the START_DATE
                start_date = league_start

                ### Search the stats of the given player ID to fill the missing attributes for the player
                player_marketvalues = get_player_marketvalue(
                    user_token, transfer["playerId"]
                )

                ### Set the price to the START_DATE value in the player_marketvalues list
                ### Do this because the player was assigned at the start of the season
                for marketValue in player_marketvalues:
                    ### Convert the Julian date to a standard date
                    market_value_date = julian_to_date(marketValue["dt"])

                    if market_value_date == start_date:
                        price = marketValue["mv"]
                        logging.debug(
                            f"Starter player {transfer['firstName']} {transfer['lastName']} was sold! Market value on START_DATE {start_date}: {price}€."
                        )
                        break

                ### If an unmatched sell transfer is found, a simulated buy transfer is created with some default values
                date = datetime.strptime(
                    league_start, "%Y-%m-%dT%H:%M:%SZ"
                ).isoformat()  # Format 2025-08-07T16:00:08Z
                price = 0
                buy_transfer = {
                    "date": date,
                    "type": "assigned_at_start",
                    "user": transfer["user"],
                    "tradePartner": "Kickbase",
                    "price": price,
                    "playerId": transfer["playerId"],
                    "teamId": transfer["teamId"],
                    "firstName": transfer["firstName"],
                    "lastName": transfer["lastName"],
                }

                turnovers.append((buy_transfer, transfer))

        final_turnovers += turnovers
    transfer_diffs: dict[str, list[dict[str, int]]] = defaultdict(list)
    for buy, sell in final_turnovers:
        if buy["tradePartner"] == "Kickbase" and buy["price"] == 0:
            continue
        transfer_diff = sell["price"] - buy["price"]
        transfer_diffs[buy["user"]].append({f"{buy['lastName']}": transfer_diff})
    logging.info("Got all turnovers.")
    for user in user_table.values():
        user_transfers = [
            t
            for t in transfers
            if (t["user"] == user.name and t["type"] == "buy")
            or (t["tradePartner"] == user.name and t["type"] == "sell")
        ]
        biggest_overpay_transfer = max(
            user_transfers,
            key=lambda t: t["price"] - t["marketPrice"],
            default={"price": 0, "marketPrice": 0},
        )
        if biggest_overpay_transfer != {"price": 0, "marketPrice": 0}:
            user.biggest_overpay = (
                biggest_overpay_transfer["price"]
                - biggest_overpay_transfer["marketPrice"]
            )
            user.biggest_overpay_player = f"{biggest_overpay_transfer['lastName']}"
        transfer_diffs_user = transfer_diffs[user.name]
        biggest_win_user = max(
            transfer_diffs_user, key=lambda x: list(x.values())[0], default={"": 0}
        )
        user.biggest_win = (
            biggest_win_user[list(biggest_win_user.keys())[0]]
            if biggest_win_user
            else 0
        )
        user.biggest_win_player = (
            f"{list(biggest_win_user.keys())[0]}" if biggest_win_user else "Unknown"
        )
        biggest_loss_user = min(
            transfer_diffs_user, key=lambda x: list(x.values())[0], default={"": 0}
        )
        user.biggest_lose = (
            biggest_loss_user[list(biggest_loss_user.keys())[0]]
            if biggest_loss_user
            else 0
        )
        user.biggest_lose_player = (
            f"{list(biggest_loss_user.keys())[0]}" if biggest_loss_user else "Unknown"
        )
    ### Save to file + timestamp
    with open("turnovers.json", "w") as f:
        json.dump(final_turnovers, f, indent=4)


def get_match_days(token: str, competition_id: int = 1) -> tuple:
    """### Fetch all matches for every match day in the current season and save to JSON

    Args:
        token (str): The user's kkstrauth token
        competition_id (int): The competition ID (default: 1 which is the Bundesliga)

    Returns:
        tuple: A tuple containing the current match day number and a list of dictionaries. Each dictionary contains the match day number, the start date & time of the first match, and the start date & time of the last match.
    """
    url = f"https://api.kickbase.com/v4/competitions/{competition_id}/matchdays"
    response = call_api(token, url)
    match_days = []
    current_match_day = response["day"]

    if response["it"]:
        for match_day in response["it"]:
            first_match = match_day["it"][0][
                "dt"
            ]  ### Start date & time of the first match
            last_match = match_day["it"][-1][
                "dt"
            ]  ### Start date & time of the last match

            match_days.append(
                {
                    "day": match_day["day"],
                    "firstMatch": first_match,
                    "lastMatch": last_match,
                }
            )

    logging.info("Match days fetched.")

    return current_match_day, match_days


def get_team_value_per_match_day(
    user_token: str, selected_league: object, userlist: dict[int, UserTable]
) -> tuple[dict, str]:
    """### Calculates the team value per match day for all users in the league.

    Args:
        user_token (str): The user's kkstrauth token.
        selected_league (object): The league the user wants to get data from for the frontend.
    """
    logging.info("Calculating team value per match day...")

    final_team_value = {}

    ### Get all match days of the season
    current_match_day, match_days_list = get_match_days(user_token)

    for user_id, user_info in userlist.items():
        user_name = user_info.name
        ### Get the team value for each match day
        team_value = {match_day: 0 for match_day in range(1, current_match_day + 1)}

        ### Loop through all match days
        for match_day in match_days_list:
            ### Skip processing if the match day is in the future
            if match_day["day"] > current_match_day:
                continue
            query_params = f"?dayNumber={match_day['day']}"
            url = f"https://api.kickbase.com/v4/leagues/{selected_league}/ranking/{query_params}"
            ranking_data = call_api(user_token, url)
            team_value_on_match_day = 0

            for real_user in ranking_data["us"]:
                if real_user["i"] == user_id:
                    team_value_on_match_day = real_user["tv"]
                    break

            if len(team_value) >= match_day["day"]:
                team_value[match_day["day"]] = team_value_on_match_day

        final_team_value[user_name] = team_value

    logging.info("Calculated team value per match day.")
    with open("team_values.json", "w") as f:
        json.dump(final_team_value, f, indent=4)
    return final_team_value, current_match_day


def get_initial_team_value(
    token: str, user_id: int, selected_league: object, start_date: str
) -> int:
    """### Fetches the initial team for the user in the selected league.

    Args:
        token (str): The user's kkstrauth token.
        user_id (int): User for which to fetch inital team.
        selected_league (object): The league the user wants to get data from for the frontend.
        start_date (str): Start date of the league.

    Returns:
        dict: Value of initial team
    """
    logging.info("Fetching initial team...")
    start_point = 0
    start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ").strftime(
        "%d.%m.%Y"
    )
    url = f"https://api.kickbase.com/v4/leagues/{selected_league}/managers/{user_id}/transfer?start={start_point}"
    result = []
    init_team_value = 0
    while response := call_api(token, url):
        if not response.get("it"):
            break
        result.extend(response.get("it", []))
        start_point += 25
        url = f"https://api.kickbase.com/v4/leagues/{selected_league}/managers/{user_id}/transfer?start={start_point}"
    for transfer in result:
        if (
            transfer.get("tty") == 0 and transfer.get("trp") == 0
        ):  # Indicates that the player was a starter player.
            price = 0
            price = get_player_marketvalue_date(token, transfer["pi"], start_date)
            init_team_value += price
    return init_team_value


def build_table(user_table: list[dict]) -> defaultdict:
    return_table = defaultdict(list)
    for user in user_table:
        print(user)
        if "ludw1" in user.get("Name", ""):
            continue
        for key, value in user.items():
            return_table[key].append(value)
    return return_table


def main():
    user = login()
    filename = "table.html"
    update_turnovers = True
    league_id = [
        league["id"] for league in user.leagues if league["name"] == "Alex stinkt 25/26"
    ][0]
    league_start = [
        league["creation"]
        for league in user.leagues
        if league["name"] == "Alex stinkt 25/26"
    ][0]
    user_table = get_users(user.token, league_id)
    historical_team_values, current_match_day = get_team_value_per_match_day(
        user.token, league_id, user_table
    )
    get_turnovers(user.token, league_id, league_start, user_table, update_turnovers)

    for user_id, user_info in user_table.items():
        user_stats = get_user_stats(user.token, league_id, user_id)
        user_info.team_value = user_stats.get("tv", 0)
        user_info.total_points = user_stats.get("tp", 0)
        user_info.placement = user_stats.get("pl", 0)
        user_info.matchday_wins = user_stats.get("mdw", 0)
        user_team = get_user_team(user.token, league_id, user_id)
        user_info.team = user_team.get("it", [])
        user_info.bigboy = max(
            user_info.team, key=lambda x: x.get("mv", 0), default={"pn": "NA"}
        ).get("pn", "NA")
        user_info.bigboy_value = max(
            user_info.team, key=lambda x: x.get("mv", 0), default={"mv": 0}
        ).get("mv", 0)
        user_info.half_million_players = sum(
            1 for player in user_info.team if player.get("mv", 0) <= 500000
        )
        if current_match_day == 1: # Also bevor dem ersten Spieltag
            user_info.tv_change = historical_team_values[user_info.name].get(
                current_match_day
            ) - get_initial_team_value(user.token, user_id, league_id, league_start)
        else:
            user_info.tv_change = historical_team_values[user_info.name].get(
                current_match_day
            ) - historical_team_values[user_info.name].get(
                str(int(current_match_day) - 1)
            )
    print(user_table)

    table = build_table([user.return_data() for user in user_table.values()])
    with open(filename, "w", encoding="utf-8") as f:
        f.write(
            tabulate(
                table,
                headers="keys",
                tablefmt="unsafehtml",
                intfmt="d",
                floatfmt=".2f",
                numalign="center",
            )
        )
    style_table(filename)
    webbrowser.open(filename) # Öffnet direkt die Tabelle

if __name__ == "__main__":
    main()
