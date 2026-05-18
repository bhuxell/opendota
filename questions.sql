--------------------------------------------------------------------------------
/*
Question 1: Which Team Liquid player had the strongest overall performance
across their recent matches? Briefly describe which stats you used to
evaluate overall performance and why.

ANSWER: 201358612

The ranking system used here uses all computed metrics in the output shape,
prioritizing win rate as the main metric for overall performance to account for
different roles having different overall objectives (ex kd_ratio). If players
have won the same number of matches, the next metrics used are focused on their
individual stats, with a focus on a high kd_ratio as the next proxy for
performance. In the event of a tie, kills, deaths, and assists are used, with
the account_id as a final tiebreaker to ensure a deterministic ordering.

NOTE: Only the output shape metrics were used, rather than computing a
separate composite metric.
*/

with match_results as (
  select
    account_id,
    kills,
    deaths,
    assists,
    ((player_slot < 128) = radiant_win)::int as is_win
  from team_liquid_recent_matches
)

select
  account_id,
  count(*) as matches_played,
  sum(is_win) as wins,
  count(*) - sum(is_win) as losses,
  round(sum(is_win)::numeric / count(*), 2) as win_rate,
  round(avg(kills), 2) as avg_kills,
  round(avg(deaths), 2) as avg_deaths,
  round(avg(assists), 2) as avg_assists,
  round(sum(kills)::numeric / nullif(sum(deaths), 0), 2) as kd_ratio
from match_results
group by
  account_id
order by
  win_rate desc,
  kd_ratio desc,
  avg_kills desc,
  avg_deaths asc,
  avg_assists desc,
  matches_played desc,
  account_id asc -- deterministic ordering in case of total tie
;

--------------------------------------------------------------------------------
/*
Question 2: Which Team Liquid player had the best K/D ratio across their recent
matches? Players with the same K/D ratio should receive the same rank.

ANSWER: 201358612
This implements non-consecutive ranks for players with the same K/D ratio, as
opposed to using dense rank.
*/

select
  account_id,
  sum(kills) as kills,
  sum(deaths) as deaths,
  round(sum(kills)::numeric / nullif(sum(deaths), 0), 2) as kd_ratio,
  rank() over (
    order by round(sum(kills)::numeric / nullif(sum(deaths), 0), 2) desc nulls last
  ) as kd_rank
from team_liquid_recent_matches
group by
  account_id
order by
  kd_rank asc,
  account_id asc
;

--------------------------------------------------------------------------------
/*
Question 3: How does each Team Liquid player’s performance differ between wins
and losses? Briefly describe which metric is most different between wins and
losses.

ANSWER: K/D ratio shows the largest gap between wins and losses, typically
doubling or more in wins (ex. 152962063: 0.67 to 4.29, 201358612: 1.54 to
4.88). The primary driver is avg_deaths, which drops in wins for every player
on the roster (often by 2x or more). avg_kills also tends to be higher in
wins but is less consistent (60943014 averages more kills in losses), and
avg_assists varies by role.
*/

with match_results as (
  select
    account_id,
    kills,
    deaths,
    assists,
    case
      when ((player_slot < 128) = radiant_win) then 'win'
      else 'loss'
    end as match_result
  from team_liquid_recent_matches
)

select
  account_id,
  match_result,
  count(*) as matches_played,
  round(avg(kills), 2) as avg_kills,
  round(avg(deaths), 2) as avg_deaths,
  round(avg(assists), 2) as avg_assists,
  round(sum(kills)::numeric / nullif(sum(deaths), 0), 2) as kd_ratio
from match_results
group by
  account_id,
  match_result
order by
  account_id asc,
  match_result desc
;

--------------------------------------------------------------------------------
