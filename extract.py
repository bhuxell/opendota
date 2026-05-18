"""
This script is used to extract recent match data for active Team Liquid players
via the OpenDota API and export it to a CSV file.
"""

# imports ---------------------------------------------------------------------
import csv
import requests


# constants -------------------------------------------------------------------
API_BASE_URL = "https://api.opendota.com/api"
TEAMS_PATH = "/teams"
PLAYERS_PATH = "/players"
RECENT_MATCHES_PATH = "/recentMatches"
REQUEST_TIMEOUT = 60

TEAM_NAME = "Team Liquid"
MATCHES_PER_PLAYER = 5
OUTPUT_CSV = "matches.csv"


# functions -------------------------------------------------------------------
def get_team_id(team_name: str) -> int:
    """
    Retrieve a team ID from OpenDota by exact team name match (case-insensitive).

    :param team_name: Team name to search for.
    :return: Matching OpenDota team ID.
    :raises ValueError: If no matching team is found.
    """
    url = f"{API_BASE_URL}{TEAMS_PATH}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    teams = response.json()
    normalized_name = team_name.strip().lower()

    team = next(
        (
            team
            for team in teams
            if team.get("name", "").strip().lower() == normalized_name
        ),
        None,
    )

    if team is None:
        raise ValueError(f"Team not found: {team_name}")

    return team["team_id"]


def get_team_player_ids(team_id: int) -> list[int]:
    """
    Get current team member account IDs from the OpenDota API.

    :param team_id: OpenDota team ID.
    :return: Current team member account IDs.
    :raises ValueError: If no current players are found.
    """
    url = f"{API_BASE_URL}{TEAMS_PATH}/{team_id}{PLAYERS_PATH}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    # OpenDota's definition of "current team member" may include
    # coaching staff or additional roster members beyond the active five.
    # This intentionally relies on the API's membership classification.
    account_ids = [
        player["account_id"]
        for player in data
        if player.get("is_current_team_member")
    ]

    if not account_ids:
        raise ValueError(f"No current players found for team_id: {team_id}")

    return account_ids


def get_player_matches(account_ids: list[int]) -> list[dict]:
    """
    Get recent matches for each player, tagged with account_id for reference.

    :param account_ids: Player account IDs.
    :return: Flattened player-match records.
    :raises ValueError: If no player matches are found.
    """
    matches = []

    for account_id in account_ids:
        url = f"{API_BASE_URL}{PLAYERS_PATH}/{account_id}{RECENT_MATCHES_PATH}"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        for match in data[:MATCHES_PER_PLAYER]:
            matches.append({"account_id": account_id, **match})

    if not matches:
        raise ValueError("No player matches found")

    return matches


def validate_required_keys(matches: list[dict]) -> None:
    """
    Row-level validation to ensure each record has non-null values
    for the required keys (account_id, match_id).

    :param matches: Player-match records to validate.
    :raises ValueError: If records are missing required keys or values.
    """
    required = {"account_id", "match_id"}
    missing = sum(1 for row in matches if not all(row.get(k) is not None for k in required))

    if missing:
        raise ValueError(f"{missing} row(s) missing required keys {required}")


def export_matches(matches: list[dict]) -> None:
    """
    Export the matches to a CSV file.

    :param matches: Player-match records to export.
    """
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matches[0].keys()))
        writer.writeheader()
        writer.writerows(matches)


def main():
    """
    Main function to extract recent match data from the OpenDota API and
    facilitate the CSV export.
    """
    print("Extracting data from OpenDota API...")
    team_id = get_team_id(TEAM_NAME)
    account_ids = get_team_player_ids(team_id)
    print(f"Found {len(account_ids)} current players for {TEAM_NAME}")
    matches = get_player_matches(account_ids)
    validate_required_keys(matches)
    export_matches(matches)
    print(f"Wrote {len(matches)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
