# OpenDota Submission
--------------------------

## How to Run
Requires Python 3.9+.
```bash
pip install -r requirements.txt
python extract.py
```

--------------------------

## Part 1: API Extraction
The first part of the assessment can be found in extract.py. This contains the logic for retrieving the data from OpenDota and formatting the output CSV. Some design notes:

### Definitions
The following definitions were used to create the output:

- Current Roster: Any player whose is_current_team_member flag is set. Depending on the team, this may result in more than 5 players. [Team Liquid](https://www.opendota.com/teams/2163/players) has one of the coaches, Jabbz, with this flag set which results in 6 players. Some heuristics like the 5 players with the most matches could be used to limit this to a more restrictive definition of roster, though this was omitted here for simplicity and to achieve a more authentic bronze-layer structure.
- Recent Matches: The first five matches returned from recentMatches per player.

### API Usage
The free tier of the OpenDota API allows for a maximum of 3000 calls per day, and 60 calls per minute. This script uses N + 2 calls end-to-end where N is the number of current players on the team (1 for team ID discovery, 1 for player ID discovery, 1 call per player to get recent matches).

Since this number is low and for an ad-hoc type of extraction would not be close to reaching these rate limits, general API considerations when considering scale (async handling, retry logic, exponential backoff, etc) were omitted for simplicity. Only a timeout was set to prevent hung connections. Additional notes on how the API was used:

- The GET /players/{account_id}/recentMatches endpoint with slicing was chosen over GET /players/{account_id}/matches with a limit because it contained additional data and was a better fit for the focus of the extraction.
- With the GET /search only applying to players, a call to GET /teams is made and results are iterated through to dynamically retrieve the ID based on matching to a defined team name constant.

### Output Design
With the focus on recent matches, and a particular note for the csv to contain match data, the output shape contains the result of the call to recentMatches with only the called account_id appended as a reference. This design would assume that detailed player data is available / modeled elsewhere and that this structure is primarily a bridge between players and recent matches. Further data available via GET /matches/{match_id} and GET /players/{account_id} was omitted for simplicity given the project scope.

### Validation
The script uses a simple validation pattern that only ensures a given record has non-null values for the main keys (account_id, match_id).

--------------------------
## Part 2: SQL

All three SQL questions and answers are included in questions.sql. Answers were derived from the provided DB Fiddle dataset using PostgreSQL v18. The answers to each question are provided below as well:

*Question 1: Which Team Liquid player had the strongest overall performance across their recent matches? Briefly describe which stats you used to evaluate overall performance and why.*

ANSWER: 201358612
The ranking system used here uses all computed metrics in the output shape, prioritizing win rate as the main metric for overall performance to account for different roles having different overall objectives (ex kd_ratio). If players have won the same number of matches, the next metrics used are focused on their individual stats, with a focus on a high kd_ratio as the next proxy for performance. In the event of a tie, kills, deaths, and assists are used, with the account_id as a final tiebreaker to ensure a deterministic ordering.

NOTE: Only the output shape metrics were used, rather than computing a separate composite metric.


*Question 2: Which Team Liquid player had the best K/D ratio across their recent matches? Players with the same K/D ratio should receive the same rank.*

ANSWER: 201358612
This implements non-consecutive ranks for players with the same K/D ratio, as opposed to using dense rank.


*Question 3: How does each Team Liquid player’s performance differ between wins and losses? Briefly describe which metric is most different between wins and losses.*

ANSWER: K/D ratio shows the largest gap between wins and losses, typically doubling or more in wins (ex. 152962063: 0.67 to 4.29, 201358612: 1.54 to 4.87). The primary driver is avg_deaths, which drops in wins for every player on the roster (often by 2x or more). avg_kills also tends to be higher in wins but is less consistent (60943014 averages more kills in losses), and avg_assists varies by role.
